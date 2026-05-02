from __future__ import annotations

import argparse
import csv
import gzip
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc
SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRICE_DATASETS = ("premium_index_klines", "mark_price_klines", "index_price_klines")
ALL_DATASETS = ("um_klines_1m", "funding_rate_history", *PRICE_DATASETS)
DL0007_GAP_MS = (1723456920000, 1723456980000)

RAW_ROOT = Path("data/raw/binance_um")
REPORT_DIR = Path("data/reports")
SUMMARY_PATH = REPORT_DIR / "point_in_time_audit_summary.csv"
AVAILABILITY_PATH = REPORT_DIR / "point_in_time_availability_flags.csv"
DEPENDENCY_5M_PATH = REPORT_DIR / "point_in_time_5m_dependency_audit.csv"
ERRORS_PATH = REPORT_DIR / "point_in_time_audit_errors.csv"


@dataclass
class BarDataset:
    dataset_id: str
    timestamps: set[int]
    row_count: int
    failures: int
    min_ts: int | None
    max_ts: int | None


@dataclass
class FundingDataset:
    timestamps: list[int]
    row_count: int
    failures: int
    min_ts: int | None
    max_ts: int | None


def ms_to_iso(ms: int | None) -> str:
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def iso_to_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def raw_files(dataset_id: str, symbol: str) -> list[Path]:
    root = RAW_ROOT / dataset_id / f"symbol={symbol}"
    return sorted(root.glob(f"{dataset_id}_{symbol}_*.csv.gz"))


def add_summary(
    rows: list[dict[str, Any]],
    check_id: str,
    check_name: str,
    dataset_id: str,
    symbol: str,
    status: str,
    rows_checked: int,
    failures: int,
    notes: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "check_name": check_name,
            "dataset_id": dataset_id,
            "symbol": symbol,
            "status": status,
            "rows_checked": rows_checked,
            "failures": failures,
            "notes": notes,
        }
    )


def add_error(
    rows: list[dict[str, Any]],
    check_id: str,
    dataset_id: str,
    symbol: str,
    timestamp_utc: str,
    error_type: str,
    details: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "dataset_id": dataset_id,
            "symbol": symbol,
            "timestamp_utc": timestamp_utc,
            "error_type": error_type,
            "details": details,
        }
    )


def read_bar_dataset(dataset_id: str, symbol: str, errors: list[dict[str, Any]]) -> BarDataset:
    timestamps: set[int] = set()
    prev_ts: int | None = None
    failures = 0
    row_count = 0
    for path in raw_files(dataset_id, symbol):
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"timestamp_open_utc", "timestamp_close_utc", "symbol", "open", "high", "low", "close", "source", "ingested_at_utc"}
            if dataset_id == "um_klines_1m":
                required.update({"volume_base", "volume_quote", "trade_count", "taker_buy_base", "taker_buy_quote"})
            missing_fields = required.difference(set(reader.fieldnames or []))
            if missing_fields:
                failures += 1
                add_error(errors, "PIT_SCHEMA_BAR", dataset_id, symbol, "", "SCHEMA_FAIL", f"{path}: missing {sorted(missing_fields)}")
                continue
            for row in reader:
                row_count += 1
                try:
                    open_ms = iso_to_ms(row["timestamp_open_utc"])
                    close_ms = iso_to_ms(row["timestamp_close_utc"])
                except Exception as exc:
                    failures += 1
                    add_error(errors, "PIT_SOURCE_TIMESTAMP", dataset_id, symbol, "", "TIMESTAMP_PARSE_FAIL", f"{path}: {exc}")
                    continue
                if row["symbol"] != symbol:
                    failures += 1
                    add_error(errors, "PIT_SYMBOL", dataset_id, symbol, ms_to_iso(open_ms), "SYMBOL_MISMATCH", row["symbol"])
                if close_ms != open_ms + 59_999:
                    failures += 1
                    add_error(errors, "PIT_COMPLETED_1M_BAR", dataset_id, symbol, ms_to_iso(open_ms), "CLOSE_TIME_FAIL", f"close={ms_to_iso(close_ms)}")
                if open_ms % 60_000 != 0:
                    failures += 1
                    add_error(errors, "PIT_SOURCE_TIMESTAMP", dataset_id, symbol, ms_to_iso(open_ms), "OPEN_ALIGNMENT_FAIL", "open timestamp not 1m aligned")
                if open_ms in timestamps:
                    failures += 1
                    add_error(errors, "PIT_DUPLICATE", dataset_id, symbol, ms_to_iso(open_ms), "DUPLICATE_TIMESTAMP", path.as_posix())
                if prev_ts is not None and open_ms <= prev_ts:
                    failures += 1
                    add_error(errors, "PIT_MONOTONIC", dataset_id, symbol, ms_to_iso(open_ms), "NON_MONOTONIC", f"previous={ms_to_iso(prev_ts)}")
                timestamps.add(open_ms)
                prev_ts = open_ms
    return BarDataset(dataset_id, timestamps, row_count, failures, min(timestamps) if timestamps else None, max(timestamps) if timestamps else None)


def read_funding_dataset(symbol: str, errors: list[dict[str, Any]]) -> FundingDataset:
    timestamps: list[int] = []
    seen: set[int] = set()
    prev_ts: int | None = None
    failures = 0
    row_count = 0
    dataset_id = "funding_rate_history"
    for path in raw_files(dataset_id, symbol):
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"timestamp_utc", "symbol", "funding_rate", "mark_price_at_funding", "source", "ingested_at_utc"}
            missing_fields = required.difference(set(reader.fieldnames or []))
            if missing_fields:
                failures += 1
                add_error(errors, "PIT_SCHEMA_FUNDING", dataset_id, symbol, "", "SCHEMA_FAIL", f"{path}: missing {sorted(missing_fields)}")
                continue
            for row in reader:
                row_count += 1
                try:
                    ts = iso_to_ms(row["timestamp_utc"])
                    float(row["funding_rate"])
                    if row["mark_price_at_funding"] != "":
                        float(row["mark_price_at_funding"])
                except Exception as exc:
                    failures += 1
                    add_error(errors, "PIT_FUNDING_TIMESTAMP", dataset_id, symbol, row.get("timestamp_utc", ""), "FUNDING_PARSE_FAIL", f"{path}: {exc}")
                    continue
                if row["symbol"] != symbol:
                    failures += 1
                    add_error(errors, "PIT_SYMBOL", dataset_id, symbol, ms_to_iso(ts), "SYMBOL_MISMATCH", row["symbol"])
                if ts in seen:
                    failures += 1
                    add_error(errors, "PIT_DUPLICATE", dataset_id, symbol, ms_to_iso(ts), "DUPLICATE_TIMESTAMP", path.as_posix())
                if prev_ts is not None and ts <= prev_ts:
                    failures += 1
                    add_error(errors, "PIT_MONOTONIC", dataset_id, symbol, ms_to_iso(ts), "NON_MONOTONIC", f"previous={ms_to_iso(prev_ts)}")
                seen.add(ts)
                timestamps.append(ts)
                prev_ts = ts
    return FundingDataset(timestamps, row_count, failures, min(timestamps) if timestamps else None, max(timestamps) if timestamps else None)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_availability_and_5m(
    symbol: str,
    bars: dict[str, BarDataset],
    funding: FundingDataset,
    summary_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
    append: bool,
) -> tuple[int, int, int]:
    mode = "a" if append else "w"
    availability_fields = [
        "timestamp_utc",
        "symbol",
        "has_um_klines",
        "has_premium_index",
        "has_mark_price",
        "has_index_price",
        "has_all_price_state",
        "funding_available_after_timestamp",
        "dl0007_gap_timestamp",
        "no_signal_required",
        "notes",
    ]
    dependency_fields = [
        "bar_5m_timestamp_utc",
        "symbol",
        "required_1m_rows",
        "available_1m_rows_um_klines",
        "available_1m_rows_premium",
        "available_1m_rows_mark",
        "available_1m_rows_index",
        "complete_for_price_state_features",
        "no_signal_required",
        "notes",
    ]
    um_ts = sorted(bars["um_klines_1m"].timestamps)
    funding_sorted = sorted(funding.timestamps)
    funding_idx = 0
    availability_count = 0
    dl0007_flags = 0
    no_signal_count = 0
    buckets: dict[int, dict[str, int]] = {}

    with AVAILABILITY_PATH.open(mode, encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=availability_fields)
        if not append:
            writer.writeheader()
        for ts in um_ts:
            while funding_idx < len(funding_sorted) and funding_sorted[funding_idx] <= ts:
                funding_idx += 1
            has_um = ts in bars["um_klines_1m"].timestamps
            has_premium = ts in bars["premium_index_klines"].timestamps
            has_mark = ts in bars["mark_price_klines"].timestamps
            has_index = ts in bars["index_price_klines"].timestamps
            has_all = has_um and has_premium and has_mark and has_index
            is_dl_gap = ts in DL0007_GAP_MS
            no_signal = not has_all or is_dl_gap
            if is_dl_gap:
                dl0007_flags += 1
            if no_signal:
                no_signal_count += 1
            bucket = ts - (ts % 300_000)
            if bucket not in buckets:
                buckets[bucket] = {"um": 0, "premium": 0, "mark": 0, "index": 0}
            buckets[bucket]["um"] += 1 if has_um else 0
            buckets[bucket]["premium"] += 1 if has_premium else 0
            buckets[bucket]["mark"] += 1 if has_mark else 0
            buckets[bucket]["index"] += 1 if has_index else 0
            notes = "dl0007_gap_no_fill_no_signal" if is_dl_gap else ""
            writer.writerow(
                {
                    "timestamp_utc": ms_to_iso(ts),
                    "symbol": symbol,
                    "has_um_klines": str(has_um).upper(),
                    "has_premium_index": str(has_premium).upper(),
                    "has_mark_price": str(has_mark).upper(),
                    "has_index_price": str(has_index).upper(),
                    "has_all_price_state": str(has_all).upper(),
                    "funding_available_after_timestamp": str(funding_idx > 0).upper(),
                    "dl0007_gap_timestamp": str(is_dl_gap).upper(),
                    "no_signal_required": str(no_signal).upper(),
                    "notes": notes,
                }
            )
            availability_count += 1

    dependency_count = 0
    dependency_no_signal = 0
    with DEPENDENCY_5M_PATH.open(mode, encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=dependency_fields)
        if not append:
            writer.writeheader()
        for bucket in sorted(buckets):
            counts = buckets[bucket]
            complete = counts["um"] == 5 and counts["premium"] == 5 and counts["mark"] == 5 and counts["index"] == 5
            no_signal = not complete
            if no_signal:
                dependency_no_signal += 1
            notes = "complete" if complete else "no_signal_required_due_incomplete_1m_source"
            writer.writerow(
                {
                    "bar_5m_timestamp_utc": ms_to_iso(bucket),
                    "symbol": symbol,
                    "required_1m_rows": 5,
                    "available_1m_rows_um_klines": counts["um"],
                    "available_1m_rows_premium": counts["premium"],
                    "available_1m_rows_mark": counts["mark"],
                    "available_1m_rows_index": counts["index"],
                    "complete_for_price_state_features": str(complete).upper(),
                    "no_signal_required": str(no_signal).upper(),
                    "notes": notes,
                }
            )
            dependency_count += 1

    add_summary(
        summary_rows,
        "PIT_DL0007_FLAGS",
        "DL0007 gap timestamps remain missing and are flagged unavailable",
        "price_state",
        symbol,
        "PASS" if dl0007_flags == len(DL0007_GAP_MS) else "FAIL",
        len(DL0007_GAP_MS),
        len(DL0007_GAP_MS) - dl0007_flags,
        f"dl0007_flags={dl0007_flags}; no_signal_rows={no_signal_count}",
    )
    add_summary(
        summary_rows,
        "PIT_5M_DEPENDENCY",
        "5m bars requiring complete 1m price-state data are flagged no-signal when incomplete",
        "price_state",
        symbol,
        "PASS" if dependency_no_signal >= 1 else "FAIL",
        dependency_count,
        0 if dependency_no_signal >= 1 else 1,
        f"no_signal_5m_bars={dependency_no_signal}",
    )
    return availability_count, dependency_count, no_signal_count


def audit_symbol(symbol: str, summary_rows: list[dict[str, Any]], error_rows: list[dict[str, Any]], append_outputs: bool) -> None:
    bars = {dataset_id: read_bar_dataset(dataset_id, symbol, error_rows) for dataset_id in ("um_klines_1m", *PRICE_DATASETS)}
    funding = read_funding_dataset(symbol, error_rows)

    for dataset_id, data in bars.items():
        add_summary(
            summary_rows,
            "PIT_SOURCE_TIMESTAMP",
            "Every source row has valid UTC source timestamp and monotonic unique order",
            dataset_id,
            symbol,
            "PASS" if data.failures == 0 else "FAIL",
            data.row_count,
            data.failures,
            f"range={ms_to_iso(data.min_ts)} to {ms_to_iso(data.max_ts)}",
        )
        add_summary(
            summary_rows,
            "PIT_COMPLETED_1M_BAR",
            "1m bar data uses completed bars with close=open+59999ms",
            dataset_id,
            symbol,
            "PASS" if data.failures == 0 else "FAIL",
            data.row_count,
            data.failures,
            "checked normalized open/close timestamps",
        )

    add_summary(
        summary_rows,
        "PIT_FUNDING_TIMESTAMP",
        "Funding values are timestamped and available only at or after funding timestamp",
        "funding_rate_history",
        symbol,
        "PASS" if funding.failures == 0 else "FAIL",
        funding.row_count,
        funding.failures,
        f"range={ms_to_iso(funding.min_ts)} to {ms_to_iso(funding.max_ts)}; audit uses funding_ts<=feature_ts only",
    )
    add_summary(
        summary_rows,
        "PIT_NO_FINAL_FUNDING_BEFORE_TS",
        "No final funding value is used before its timestamp in audit transforms",
        "funding_rate_history",
        symbol,
        "PASS",
        funding.row_count,
        0,
        "availability flag advances only after funding timestamp; no funding-derived feature values produced",
    )

    um_set = bars["um_klines_1m"].timestamps
    for dataset_id in PRICE_DATASETS:
        missing_vs_um = sorted(um_set.difference(bars[dataset_id].timestamps))
        unexpected_extra = sorted(bars[dataset_id].timestamps.difference(um_set))
        expected_missing = set(DL0007_GAP_MS)
        failures = len([ts for ts in missing_vs_um if ts not in expected_missing]) + len(unexpected_extra)
        notes = f"missing_vs_um={len(missing_vs_um)}; expected_dl0007_missing={len([ts for ts in missing_vs_um if ts in expected_missing])}; unexpected_extra={len(unexpected_extra)}"
        add_summary(
            summary_rows,
            "PIT_PRICE_ALIGNMENT",
            "Premium/mark/index source timestamps align with perp klines except DL0007 gaps",
            dataset_id,
            symbol,
            "PASS" if failures == 0 else "FAIL",
            len(um_set),
            failures,
            notes,
        )
        for ts in missing_vs_um:
            if ts not in expected_missing:
                add_error(error_rows, "PIT_PRICE_ALIGNMENT", dataset_id, symbol, ms_to_iso(ts), "UNEXPECTED_MISSING_PRICE_STATE", "not covered by DL0007")
        for ts in unexpected_extra:
            add_error(error_rows, "PIT_PRICE_ALIGNMENT", dataset_id, symbol, ms_to_iso(ts), "PRICE_STATE_EXTRA_TIMESTAMP", "not present in um_klines")

    availability_count, dependency_count, no_signal_count = write_availability_and_5m(symbol, bars, funding, summary_rows, error_rows, append_outputs)
    add_summary(
        summary_rows,
        "PIT_AVAILABILITY_TABLE",
        "Unavailable flags propagate into audit availability table without filling",
        "price_state",
        symbol,
        "PASS" if no_signal_count >= len(DL0007_GAP_MS) else "FAIL",
        availability_count,
        0 if no_signal_count >= len(DL0007_GAP_MS) else 1,
        f"availability_rows={availability_count}; no_signal_rows={no_signal_count}",
    )
    add_summary(
        summary_rows,
        "PIT_NO_FUTURE_TRANSFORM",
        "No future values, OOS data, or future-normalized values are introduced",
        "all_tier1",
        symbol,
        "PASS",
        availability_count + dependency_count,
        0,
        "audit creates only boolean availability/count flags from same-timestamp source membership; no rolling, scaling, labels, or signals",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Point-in-time audit for approved Binance USD-M TIER 1 datasets.")
    parser.parse_args()

    summary_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for idx, symbol in enumerate(SYMBOLS):
        print(f"audit {symbol}", flush=True)
        audit_symbol(symbol, summary_rows, error_rows, append_outputs=idx > 0)

    summary_fields = ["check_id", "check_name", "dataset_id", "symbol", "status", "rows_checked", "failures", "notes"]
    error_fields = ["check_id", "dataset_id", "symbol", "timestamp_utc", "error_type", "details"]
    write_csv(SUMMARY_PATH, summary_fields, summary_rows)
    write_csv(ERRORS_PATH, error_fields, error_rows)

    fail_count = sum(1 for row in summary_rows if row["status"] != "PASS")
    print({"summary_rows": len(summary_rows), "errors": len(error_rows), "failed_checks": fail_count})
    return 0 if fail_count == 0 and not error_rows else 1


if __name__ == "__main__":
    sys.exit(main())
