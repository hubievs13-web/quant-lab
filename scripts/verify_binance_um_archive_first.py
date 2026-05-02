from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SYMBOLS = ("BTCUSDT", "ETHUSDT")
OUT_DIR = Path("data_inventory")
UTC = timezone.utc

MS_2021_01_01 = 1609459200000
MS_2021_02_01 = 1612137600000 - 1
MS_2024_01_01 = 1704067200000
MS_2024_02_01 = 1706745600000 - 1


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    archive_template: str | None
    rest_base: str | None
    rest_kind: str
    expected_interval: str
    expected_interval_ms: int | None
    expected_schema_count: int | None
    expected_schema_fields: str


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_iso() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")


def ms_to_iso(ms: int | None) -> str:
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat().replace("+00:00", "Z")


def latest_completed_month() -> tuple[int, int]:
    today = now_utc()
    year = today.year
    month = today.month - 1
    if month == 0:
        year -= 1
        month = 12
    return year, month


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, *, method: str, timeout: float, retries: int, max_bytes: int | None = None) -> tuple[int, bytes, str]:
    last_status = 0
    last_body = b""
    last_error = ""
    for attempt in range(retries + 1):
        req = Request(url, method=method, headers={"User-Agent": "quant-lab-archive-first/1.0"})
        try:
            with urlopen(req, timeout=timeout) as response:
                if method == "HEAD":
                    return response.status, b"", ""
                if max_bytes is None:
                    body = response.read()
                else:
                    body = response.read(max_bytes + 1)
                    if len(body) > max_bytes:
                        return response.status, body[:max_bytes], "TRUNCATED"
                return response.status, body, ""
        except HTTPError as exc:
            last_status = exc.code
            try:
                last_body = exc.read(4096)
            except Exception:
                last_body = b""
            last_error = f"HTTPError: {exc.reason}"
            if exc.code == 404:
                break
        except URLError as exc:
            last_status = 0
            last_body = b""
            last_error = f"URLError: {exc.reason}"
        except Exception as exc:
            last_status = 0
            last_body = b""
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(0.5 * (2 ** attempt))
    return last_status, last_body, last_error


def archive_url(template: str, symbol: str, year: int, month: int) -> str:
    return template.format(SYMBOL=symbol, PAIR=symbol, YYYY=f"{year:04d}", MM=f"{month:02d}")


def status_label(status: int, error: str = "") -> str:
    if status == 200:
        return "OK"
    if status == 404:
        return "NOT_FOUND"
    if status == 0:
        return f"ERROR:{error}" if error else "ERROR"
    return f"HTTP_{status}"


def parse_zip_sample(data: bytes, max_rows: int = 500) -> tuple[list[list[str]], str]:
    rows: list[list[str]] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            return rows, "NO_CSV_IN_ZIP"
        with zf.open(csv_names[0]) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8", newline="")
            reader = csv.reader(text)
            for raw in reader:
                if not raw:
                    continue
                if raw[0].strip().lower() in {"open_time", "open time", "timestamp"}:
                    continue
                rows.append(raw)
                if len(rows) >= max_rows:
                    break
    return rows, ""


def parse_rest_rows(body: bytes) -> list[Any]:
    if not body:
        return []
    payload = json.loads(body.decode("utf-8"))
    return payload if isinstance(payload, list) else []


def timestamp_from_row(row: Any, rest_kind: str) -> int | None:
    if isinstance(row, list) and row:
        try:
            return int(float(row[0]))
        except Exception:
            return None
    if isinstance(row, dict):
        key = "fundingTime" if rest_kind == "funding" else "timestamp"
        if key in row:
            try:
                return int(row[key])
            except Exception:
                return None
    return None


def observed_fields_from_row(row: Any) -> str:
    if isinstance(row, list):
        return ",".join(f"col{i}" for i in range(len(row)))
    if isinstance(row, dict):
        return ",".join(row.keys())
    return ""


def gap_stats(timestamps: list[int], interval_ms: int | None) -> tuple[str, str, str, str]:
    if not timestamps:
        return "", "0", "0", "TRUE"
    monotonic = all(a <= b for a, b in zip(timestamps, timestamps[1:]))
    duplicates = len(timestamps) - len(set(timestamps))
    missing = 0
    expected = ""
    if interval_ms:
        unique_sorted = sorted(set(timestamps))
        expected = str(((max(unique_sorted) - min(unique_sorted)) // interval_ms) + 1)
        for prev, curr in zip(unique_sorted, unique_sorted[1:]):
            gap = curr - prev
            if gap > interval_ms:
                missing += max(0, (gap // interval_ms) - 1)
    return expected, str(missing), str(duplicates), str(monotonic).upper()


def rest_url(dataset: Dataset, symbol: str, start_ms: int, end_ms: int) -> str:
    if dataset.rest_base is None:
        return ""
    if dataset.rest_kind == "funding":
        params = {"symbol": symbol, "startTime": start_ms, "endTime": end_ms, "limit": 1000}
    elif dataset.rest_kind == "index":
        params = {"pair": symbol, "interval": "1m", "startTime": start_ms, "endTime": min(start_ms + 3_600_000 - 1, end_ms), "limit": 60}
    else:
        params = {"symbol": symbol, "interval": "1m", "startTime": start_ms, "endTime": min(start_ms + 3_600_000 - 1, end_ms), "limit": 60}
    return f"{dataset.rest_base}?{urlencode(params)}"


def latest_rest_url(dataset: Dataset, symbol: str) -> str:
    if dataset.rest_base is None:
        return ""
    if dataset.rest_kind == "funding":
        params = {"symbol": symbol, "limit": 20}
    elif dataset.rest_kind == "index":
        params = {"pair": symbol, "interval": "1m", "limit": 60}
    else:
        params = {"symbol": symbol, "interval": "1m", "limit": 60}
    return f"{dataset.rest_base}?{urlencode(params)}"


def datasets() -> list[Dataset]:
    kline_fields = "open_time,open,high,low,close,volume,close_time,quote_volume,trade_count,taker_buy_base,taker_buy_quote,ignore"
    price_kline_fields = "open_time,open,high,low,close,ignore_1,close_time,ignore_2,ignore_3,ignore_4,ignore_5,ignore_6"
    return [
        Dataset(
            "um_klines_1m",
            "https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/klines",
            "symbol_kline",
            "1m",
            60_000,
            12,
            kline_fields,
        ),
        Dataset(
            "funding_rate_history",
            "https://data.binance.vision/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/fundingRate",
            "funding",
            "8h_expected",
            28_800_000,
            None,
            "symbol,fundingRate,fundingTime,markPrice",
        ),
        Dataset(
            "premium_index_klines",
            "https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/premiumIndexKlines",
            "symbol_kline",
            "1m",
            60_000,
            12,
            price_kline_fields,
        ),
        Dataset(
            "mark_price_klines",
            "https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/markPriceKlines",
            "symbol_kline",
            "1m",
            60_000,
            12,
            price_kline_fields,
        ),
        Dataset(
            "index_price_klines",
            "https://data.binance.vision/data/futures/um/monthly/indexPriceKlines/{PAIR}/1m/{PAIR}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/indexPriceKlines",
            "index",
            "1m",
            60_000,
            12,
            price_kline_fields,
        ),
    ]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive-first Binance USD-M inventory verification.")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--sample-archive-bytes", type=int, default=15_000_000)
    args = parser.parse_args()

    latest_year, latest_month = latest_completed_month()
    checked_at = now_iso()
    source_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    checksum_rows: list[dict[str, Any]] = []
    evidence: dict[str, dict[str, bool]] = {}

    for dataset in datasets():
        evidence[dataset.dataset_id] = {}
        for symbol in SYMBOLS:
            notes: list[str] = []
            url_2021 = archive_url(dataset.archive_template, symbol, 2021, 1) if dataset.archive_template else ""
            url_2024 = archive_url(dataset.archive_template, symbol, 2024, 1) if dataset.archive_template else ""
            url_latest = archive_url(dataset.archive_template, symbol, latest_year, latest_month) if dataset.archive_template else ""

            archive_statuses: dict[str, tuple[int, str]] = {}
            for label, url in (("2021_01", url_2021), ("2024_01", url_2024), ("latest", url_latest)):
                if not url:
                    archive_statuses[label] = (0, "NO_ARCHIVE_TEMPLATE")
                    continue
                status, body, err = fetch(url, method="HEAD", timeout=args.timeout, retries=args.retries)
                archive_statuses[label] = (status, status_label(status, err))
                checksum_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": url,
                        "check_type": f"archive_head_{label}",
                        "bytes": 0,
                        "sha256": "",
                        "checked_at_utc": checked_at,
                        "notes": status_label(status, err),
                    }
                )
                checksum_url = f"{url}.CHECKSUM"
                c_status, c_body, c_err = fetch(checksum_url, method="GET", timeout=args.timeout, retries=args.retries, max_bytes=4096)
                checksum_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": checksum_url,
                        "check_type": f"checksum_get_{label}",
                        "bytes": len(c_body),
                        "sha256": sha256_bytes(c_body) if c_body else "",
                        "checked_at_utc": checked_at,
                        "notes": status_label(c_status, c_err),
                    }
                )

            sample_rows: list[Any] = []
            sample_source_url = ""
            sample_notes = ""
            if archive_statuses["2024_01"][0] == 200 and url_2024:
                status, body, err = fetch(url_2024, method="GET", timeout=args.timeout, retries=args.retries, max_bytes=args.sample_archive_bytes)
                sample_source_url = url_2024
                checksum_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": url_2024,
                        "check_type": "archive_sample_get_2024_01",
                        "bytes": len(body),
                        "sha256": sha256_bytes(body) if body else "",
                        "checked_at_utc": checked_at,
                        "notes": status_label(status, err),
                    }
                )
                if status == 200 and body:
                    try:
                        parsed_rows, sample_notes = parse_zip_sample(body)
                        sample_rows = parsed_rows
                    except Exception as exc:
                        sample_notes = f"zip_parse_error:{type(exc).__name__}:{exc}"
                else:
                    sample_notes = status_label(status, err)

            rest_fallback = ""
            rest_status_text = ""
            rest_rows: list[Any] = []
            rest_windows_ok: list[str] = []
            if not sample_rows or dataset.dataset_id == "funding_rate_history":
                rest_checks = (
                    ("2021_01", MS_2021_01_01, MS_2021_02_01),
                    ("2024_01", MS_2024_01_01, MS_2024_02_01),
                    ("latest", 0, 0),
                )
            else:
                rest_checks = (("latest", 0, 0),)
            for label, start_ms, end_ms in rest_checks:
                    url = latest_rest_url(dataset, symbol) if label == "latest" else rest_url(dataset, symbol, start_ms, end_ms)
                    if not rest_fallback:
                        rest_fallback = url
                    status, body, err = fetch(url, method="GET", timeout=args.timeout, retries=args.retries, max_bytes=2_000_000)
                    if label == "2024_01" or not rest_status_text:
                        rest_status_text = status_label(status, err)
                    checksum_rows.append(
                        {
                            "dataset_id": dataset.dataset_id,
                            "symbol": symbol,
                            "source_url": url,
                            "check_type": f"rest_fallback_{label}",
                            "bytes": len(body),
                            "sha256": sha256_bytes(body) if body else "",
                            "checked_at_utc": checked_at,
                            "notes": status_label(status, err),
                        }
                    )
                    if status == 200:
                        try:
                            rows = parse_rest_rows(body)
                            if rows:
                                rest_windows_ok.append(label)
                                if not rest_rows:
                                    rest_rows = rows
                        except Exception as exc:
                            notes.append(f"rest_{label}_parse_error:{exc}")
            if not rest_status_text:
                rest_status_text = "NOT_USED"

            rows_for_schema = sample_rows or rest_rows
            timestamps = [ts for ts in (timestamp_from_row(row, dataset.rest_kind) for row in rows_for_schema) if ts is not None]
            observed_schema = observed_fields_from_row(rows_for_schema[0]) if rows_for_schema else ""
            schema_ok = dataset.expected_schema_count is None or (rows_for_schema and len(rows_for_schema[0]) == dataset.expected_schema_count)
            archive_2021_ok = archive_statuses["2021_01"][0] == 200
            archive_2024_ok = archive_statuses["2024_01"][0] == 200
            archive_latest_ok = archive_statuses["latest"][0] == 200
            rest_all_ok = {"2021_01", "2024_01", "latest"}.issubset(set(rest_windows_ok))
            latest_ok = archive_latest_ok or "latest" in rest_windows_ok
            symbol_enough = ((archive_2024_ok and latest_ok and (archive_2021_ok or dataset.dataset_id == "funding_rate_history")) or rest_all_ok) and bool(rows_for_schema) and bool(schema_ok)
            evidence[dataset.dataset_id][symbol] = symbol_enough

            oldest_candidates: list[int] = []
            latest_candidates: list[int] = []
            if archive_2021_ok:
                oldest_candidates.append(MS_2021_01_01)
            if timestamps:
                oldest_candidates.append(min(timestamps))
                latest_candidates.append(max(timestamps))
            if archive_latest_ok:
                latest_candidates.append(int(datetime(latest_year, latest_month, 1, tzinfo=UTC).timestamp() * 1000))
            if "latest" in rest_windows_ok and rest_rows:
                latest_rest_timestamps = [ts for ts in (timestamp_from_row(row, dataset.rest_kind) for row in rest_rows) if ts is not None]
                if latest_rest_timestamps:
                    latest_candidates.append(max(latest_rest_timestamps))

            expected_rows, missing_rows, duplicate_rows, monotonic = gap_stats(timestamps, dataset.expected_interval_ms)
            gap_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "sample_window": sample_source_url or rest_fallback,
                    "expected_interval": dataset.expected_interval,
                    "expected_rows": expected_rows,
                    "observed_rows": len(rows_for_schema),
                    "missing_rows": missing_rows,
                    "duplicate_rows": duplicate_rows,
                    "timestamp_monotonic": monotonic,
                    "status": "OK" if rows_for_schema and missing_rows == "0" and duplicate_rows == "0" and monotonic == "TRUE" else ("NO_SAMPLE" if not rows_for_schema else "CHECK"),
                    "notes": sample_notes or "Small sample only; not a full historical gap audit.",
                }
            )

            notes.extend(
                [
                    f"archive_2021={archive_statuses['2021_01'][1]}",
                    f"archive_2024={archive_statuses['2024_01'][1]}",
                    f"archive_latest={archive_statuses['latest'][1]}",
                    f"rest_windows_ok={','.join(rest_windows_ok) if rest_windows_ok else 'none'}",
                ]
            )
            if sample_notes:
                notes.append(f"sample_note={sample_notes}")

            source_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "source_type": "archive_first_rest_fallback",
                    "archive_url_2021_01": url_2021,
                    "archive_2021_01_status": archive_statuses["2021_01"][1],
                    "archive_url_2024_01": url_2024,
                    "archive_2024_01_status": archive_statuses["2024_01"][1],
                    "latest_archive_url_checked": url_latest,
                    "latest_archive_status": archive_statuses["latest"][1],
                    "rest_fallback_url": rest_fallback,
                    "rest_fallback_status": rest_status_text,
                    "sample_rows_observed": len(rows_for_schema),
                    "oldest_available_timestamp_observed": ms_to_iso(min(oldest_candidates) if oldest_candidates else None),
                    "latest_available_timestamp_observed": ms_to_iso(max(latest_candidates) if latest_candidates else None),
                    "observed_schema_fields": observed_schema,
                    "enough_for_12m_research": "YES" if symbol_enough else "UNKNOWN",
                    "tier": "PENDING_DATASET_CLASSIFICATION",
                    "notes": " | ".join(notes),
                }
            )

    dataset_tiers: dict[str, str] = {}
    for dataset_id, by_symbol in evidence.items():
        if all(by_symbol.get(symbol, False) for symbol in SYMBOLS):
            dataset_tiers[dataset_id] = "TIER 1"
        else:
            dataset_tiers[dataset_id] = "UNKNOWN"
    for row in source_rows:
        row["tier"] = dataset_tiers[row["dataset_id"]]

    write_csv(
        OUT_DIR / "source_inventory_archive_first.csv",
        [
            "dataset_id",
            "symbol",
            "source_type",
            "archive_url_2021_01",
            "archive_2021_01_status",
            "archive_url_2024_01",
            "archive_2024_01_status",
            "latest_archive_url_checked",
            "latest_archive_status",
            "rest_fallback_url",
            "rest_fallback_status",
            "sample_rows_observed",
            "oldest_available_timestamp_observed",
            "latest_available_timestamp_observed",
            "observed_schema_fields",
            "enough_for_12m_research",
            "tier",
            "notes",
        ],
        source_rows,
    )
    write_csv(
        OUT_DIR / "gaps_report_archive_first.csv",
        [
            "dataset_id",
            "symbol",
            "sample_window",
            "expected_interval",
            "expected_rows",
            "observed_rows",
            "missing_rows",
            "duplicate_rows",
            "timestamp_monotonic",
            "status",
            "notes",
        ],
        gap_rows,
    )
    write_csv(
        OUT_DIR / "checksums_archive_first.csv",
        [
            "dataset_id",
            "symbol",
            "source_url",
            "check_type",
            "bytes",
            "sha256",
            "checked_at_utc",
            "notes",
        ],
        checksum_rows,
    )
    print("Archive-first verification complete.")
    print(json.dumps(dataset_tiers, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
