from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


UTC = timezone.utc
USER_AGENT = "quant-lab-tier1-gap-resolution/1.0"

DATASETS = ("premium_index_klines", "mark_price_klines", "index_price_klines")
SYMBOLS = ("BTCUSDT", "ETHUSDT")
MISSING_TIMESTAMPS_MS = (1723456920000, 1723456980000)
WINDOW_START_MS = 1723456800000
WINDOW_END_MS = 1723457100000
TARGET_MONTH = "2024-08"

REPORT_PATH = Path("data/reports/tier1_gap_resolution_report.csv")
RAW_AUDIT_DIR = Path("data/reports/tier1_gap_resolution_raw")
MANIFEST_PATH = Path("data/manifests/tier1_manifest.csv")
CHECKSUMS_PATH = Path("data/manifests/tier1_checksums.csv")
GAPS_PATH = Path("data/reports/tier1_gaps_report.csv")
ERRORS_PATH = Path("data/reports/tier1_ingestion_errors.csv")

NORMALIZED_COLUMNS = (
    "timestamp_open_utc",
    "timestamp_close_utc",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "source",
    "ingested_at_utc",
)


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    rest_base: str
    rest_pair_param: str


def datasets() -> list[Dataset]:
    return [
        Dataset("premium_index_klines", "https://fapi.binance.com/fapi/v1/premiumIndexKlines", "symbol"),
        Dataset("mark_price_klines", "https://fapi.binance.com/fapi/v1/markPriceKlines", "symbol"),
        Dataset("index_price_klines", "https://fapi.binance.com/fapi/v1/indexPriceKlines", "pair"),
    ]


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def iso_to_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def rest_url(dataset: Dataset, symbol: str) -> str:
    params = {
        dataset.rest_pair_param: symbol,
        "interval": "1m",
        "startTime": WINDOW_START_MS,
        "endTime": WINDOW_END_MS,
        "limit": 10,
    }
    return f"{dataset.rest_base}?{urlencode(params)}"


def local_path(dataset_id: str, symbol: str) -> Path:
    name = f"{dataset_id}_{symbol}_{TARGET_MONTH}.csv.gz"
    return Path("data/raw/binance_um") / dataset_id / f"symbol={symbol}" / name


def fetch(url: str, timeout: float, retries: int) -> tuple[int, bytes, str, int]:
    last_status = 0
    last_error = ""
    for attempt in range(retries + 1):
        req = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(req, timeout=timeout) as response:
                return response.status, response.read(), "", attempt
        except HTTPError as exc:
            last_status = exc.code
            last_error = f"HTTPError: {exc.reason}"
        except URLError as exc:
            last_status = 0
            last_error = f"URLError: {exc.reason}"
        except Exception as exc:
            last_status = 0
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(0.75 * (2**attempt))
    return last_status, b"", last_error, retries


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checksum_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_gzip_rows(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != NORMALIZED_COLUMNS:
            raise ValueError(f"unexpected normalized schema: {reader.fieldnames}")
        return list(reader)


def write_gzip_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(NORMALIZED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def normalize_rest_row(symbol: str, row: list[Any], source_url: str, ingested_at: str) -> dict[str, str]:
    if len(row) != 12:
        raise ValueError(f"unexpected REST kline width: {len(row)}")
    open_ms = int(row[0])
    close_ms = int(row[6])
    return {
        "timestamp_open_utc": ms_to_iso(open_ms),
        "timestamp_close_utc": ms_to_iso(close_ms),
        "symbol": symbol,
        "open": str(row[1]),
        "high": str(row[2]),
        "low": str(row[3]),
        "close": str(row[4]),
        "source": source_url,
        "ingested_at_utc": ingested_at,
    }


def validate_month_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    timestamps = [iso_to_ms(row["timestamp_open_utc"]) for row in rows]
    duplicates = len(timestamps) - len(set(timestamps))
    monotonic = all(a < b for a, b in zip(timestamps, timestamps[1:]))
    expected_rows = 0
    missing_rows = 0
    start_iso = ""
    end_iso = ""
    if timestamps:
        start_ms = min(timestamps)
        end_ms = max(timestamps)
        expected_rows = ((end_ms - start_ms) // 60_000) + 1
        missing_rows = expected_rows - len(set(timestamps))
        start_iso = ms_to_iso(start_ms)
        end_iso = ms_to_iso(end_ms)
    status = "OK" if rows and duplicates == 0 and monotonic and missing_rows == 0 else "INTEGRITY_FAIL"
    return {
        "start_timestamp_utc": start_iso,
        "end_timestamp_utc": end_iso,
        "row_count": len(rows),
        "expected_rows": expected_rows,
        "missing_rows": missing_rows,
        "duplicate_rows": duplicates,
        "timestamp_monotonic": str(monotonic).upper(),
        "status": status,
    }


def append_errors(new_errors: list[dict[str, Any]]) -> None:
    if not new_errors:
        return
    fields = [
        "dataset_id",
        "symbol",
        "source_url",
        "error_type",
        "error_message",
        "occurred_at_utc",
        "retry_count",
        "status",
    ]
    existing = read_csv(ERRORS_PATH) if ERRORS_PATH.exists() else []
    write_csv(ERRORS_PATH, fields, existing + new_errors)


def update_inventory_files(updated_files: dict[tuple[str, str], dict[str, Any]]) -> None:
    def with_note(existing: str, suffix: str) -> str:
        if suffix in existing:
            return existing
        return f"{existing} | {suffix}".strip(" |")

    manifest_fields = [
        "dataset_id",
        "symbol",
        "source_type",
        "source_url",
        "local_path",
        "start_timestamp_utc",
        "end_timestamp_utc",
        "row_count",
        "expected_interval",
        "schema_version",
        "observed_schema_fields",
        "status",
        "notes",
    ]
    manifest = read_csv(MANIFEST_PATH)
    for row in manifest:
        key = (row["dataset_id"], row["symbol"])
        if key not in updated_files:
            continue
        info = updated_files[key]
        if row["local_path"] != info["local_path"]:
            continue
        row["start_timestamp_utc"] = info["validation"]["start_timestamp_utc"]
        row["end_timestamp_utc"] = info["validation"]["end_timestamp_utc"]
        row["row_count"] = str(info["validation"]["row_count"])
        row["status"] = info["validation"]["status"]
        row["source_type"] = "archive_rest_gap_resolved" if info["inserted_count"] else row["source_type"]
        row["source_url"] = info["source_url"] if info["inserted_count"] else row["source_url"]
        suffix = "gap_resolution=inserted_exact_rest_rows" if info["inserted_count"] else "gap_resolution=no_insert"
        row["notes"] = with_note(row["notes"], suffix)
    write_csv(MANIFEST_PATH, manifest_fields, manifest)

    gap_fields = [
        "dataset_id",
        "symbol",
        "window_start_utc",
        "window_end_utc",
        "expected_interval",
        "expected_rows",
        "observed_rows",
        "missing_rows",
        "duplicate_rows",
        "timestamp_monotonic",
        "status",
        "notes",
    ]
    gaps = read_csv(GAPS_PATH)
    for row in gaps:
        key = (row["dataset_id"], row["symbol"])
        if key not in updated_files:
            continue
        info = updated_files[key]
        if not row["window_start_utc"].startswith("2024-08-01"):
            continue
        row["expected_rows"] = str(info["validation"]["expected_rows"])
        row["observed_rows"] = str(info["validation"]["row_count"])
        row["missing_rows"] = str(info["validation"]["missing_rows"])
        row["duplicate_rows"] = str(info["validation"]["duplicate_rows"])
        row["timestamp_monotonic"] = info["validation"]["timestamp_monotonic"]
        row["status"] = info["validation"]["status"]
        suffix = "gap_resolution=inserted_exact_rest_rows" if info["inserted_count"] else "gap_resolution=no_insert"
        row["notes"] = with_note(row["notes"], suffix)
    write_csv(GAPS_PATH, gap_fields, gaps)

    checksum_fields = [
        "dataset_id",
        "symbol",
        "local_path",
        "source_url",
        "bytes",
        "sha256",
        "created_at_utc",
        "notes",
    ]
    checksums = read_csv(CHECKSUMS_PATH)
    for row in checksums:
        key = (row["dataset_id"], row["symbol"])
        if key not in updated_files:
            continue
        info = updated_files[key]
        if row["local_path"] != info["local_path"]:
            continue
        if not info["inserted_count"]:
            continue
        row["source_url"] = info["source_url"] if info["inserted_count"] else row["source_url"]
        row["bytes"] = str(info["bytes"])
        row["sha256"] = info["sha256"]
        row["created_at_utc"] = now_iso()
        row["notes"] = info["validation"]["status"]
    write_csv(CHECKSUMS_PATH, checksum_fields, checksums)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve exact August 2024 TIER 1 price-state gaps from Binance REST.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    report_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    updated_files: dict[tuple[str, str], dict[str, Any]] = {}

    for dataset in datasets():
        for symbol in SYMBOLS:
            url = rest_url(dataset, symbol)
            print(f"resolve {dataset.dataset_id} {symbol}", flush=True)
            status, body, error, retry_count = fetch(url, args.timeout, args.retries)
            source_status = "OK" if status == 200 else (f"HTTP_{status}" if status else "ERROR")
            if status != 200:
                error_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": url,
                        "error_type": source_status,
                        "error_message": error,
                        "occurred_at_utc": now_iso(),
                        "retry_count": retry_count,
                        "status": "FAILED",
                    }
                )
                for ts_ms in MISSING_TIMESTAMPS_MS:
                    report_rows.append(
                        {
                            "dataset_id": dataset.dataset_id,
                            "symbol": symbol,
                            "missing_timestamp_utc": ms_to_iso(ts_ms),
                            "source_url": url,
                            "source_status": source_status,
                            "recovered": "FALSE",
                            "inserted": "FALSE",
                            "validation_status": "REQUEST_FAILED",
                            "notes": error,
                        }
                    )
                continue

            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as exc:
                payload = []
                error = f"{type(exc).__name__}: {exc}"
            if not isinstance(payload, list):
                payload = []
            response_by_open = {}
            schema_ok = True
            for item in payload:
                if not isinstance(item, list) or len(item) != 12:
                    schema_ok = False
                    continue
                response_by_open[int(item[0])] = item

            path = local_path(dataset.dataset_id, symbol)
            rows = read_gzip_rows(path)
            existing_by_open = {iso_to_ms(row["timestamp_open_utc"]): row for row in rows}
            recovered_rows: dict[int, dict[str, str]] = {}
            target_results: dict[int, dict[str, str]] = {}
            ingested_at = now_iso()

            for ts_ms in MISSING_TIMESTAMPS_MS:
                if ts_ms in existing_by_open:
                    target_results[ts_ms] = {
                        "recovered": "TRUE",
                        "inserted": "FALSE",
                        "validation_status": "ALREADY_PRESENT",
                        "notes": "target timestamp already present before insertion",
                    }
                    continue
                if not schema_ok:
                    target_results[ts_ms] = {
                        "recovered": "FALSE",
                        "inserted": "FALSE",
                        "validation_status": "SCHEMA_FAIL",
                        "notes": "REST response contains non-12-field kline row",
                    }
                    continue
                if ts_ms not in response_by_open:
                    target_results[ts_ms] = {
                        "recovered": "FALSE",
                        "inserted": "FALSE",
                        "validation_status": "NOT_RETURNED",
                        "notes": "exact target timestamp not returned by REST",
                    }
                    continue
                try:
                    normalized = normalize_rest_row(symbol, response_by_open[ts_ms], url, ingested_at)
                    if iso_to_ms(normalized["timestamp_open_utc"]) != ts_ms:
                        raise ValueError("normalized timestamp mismatch")
                    recovered_rows[ts_ms] = normalized
                    target_results[ts_ms] = {
                        "recovered": "TRUE",
                        "inserted": "PENDING",
                        "validation_status": "RECOVERED",
                        "notes": "exact target timestamp returned by REST",
                    }
                except Exception as exc:
                    target_results[ts_ms] = {
                        "recovered": "FALSE",
                        "inserted": "FALSE",
                        "validation_status": "VALIDATION_FAIL",
                        "notes": f"{type(exc).__name__}: {exc}",
                    }

            inserted_count = 0
            if recovered_rows:
                rows.extend(recovered_rows.values())
                rows.sort(key=lambda row: iso_to_ms(row["timestamp_open_utc"]))
                validation = validate_month_rows(rows)
                if validation["duplicate_rows"] != 0:
                    raise SystemExit(f"Refusing to write duplicates for {dataset.dataset_id} {symbol}")
                write_gzip_rows(path, rows)
                inserted_count = len(recovered_rows)
                RAW_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
                raw_path = RAW_AUDIT_DIR / f"{dataset.dataset_id}_{symbol}_{TARGET_MONTH}_rest_window.json"
                raw_path.write_bytes(body)
                audit_sha = sha256_bytes(body)
                for ts_ms in recovered_rows:
                    target_results[ts_ms]["inserted"] = "TRUE"
                    target_results[ts_ms]["validation_status"] = validation["status"]
                    target_results[ts_ms]["notes"] = f"inserted exact REST row; raw_response_sha256={audit_sha}"
            else:
                validation = validate_month_rows(rows)

            file_size, file_sha = checksum_file(path)
            updated_files[(dataset.dataset_id, symbol)] = {
                "local_path": path.as_posix(),
                "source_url": url,
                "validation": validation,
                "bytes": file_size,
                "sha256": file_sha,
                "inserted_count": inserted_count,
            }
            for ts_ms in MISSING_TIMESTAMPS_MS:
                result = target_results[ts_ms]
                report_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "missing_timestamp_utc": ms_to_iso(ts_ms),
                        "source_url": url,
                        "source_status": source_status,
                        "recovered": result["recovered"],
                        "inserted": result["inserted"],
                        "validation_status": result["validation_status"],
                        "notes": result["notes"],
                    }
                )

    report_fields = [
        "dataset_id",
        "symbol",
        "missing_timestamp_utc",
        "source_url",
        "source_status",
        "recovered",
        "inserted",
        "validation_status",
        "notes",
    ]
    write_csv(REPORT_PATH, report_fields, report_rows)
    append_errors(error_rows)
    update_inventory_files(updated_files)

    inserted = sum(1 for row in report_rows if row["inserted"] == "TRUE")
    unresolved = sum(1 for row in report_rows if row["inserted"] != "TRUE" and row["validation_status"] != "ALREADY_PRESENT")
    integrity_statuses = {info["validation"]["status"] for info in updated_files.values()}
    status_label = "PASS" if unresolved == 0 and integrity_statuses == {"OK"} and not error_rows else "PARTIAL"
    print(json.dumps({"inserted": inserted, "unresolved": unresolved, "request_errors": len(error_rows), "status": status_label}, sort_keys=True))
    return 0 if status_label == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
