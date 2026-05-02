from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


UTC = timezone.utc
SYMBOLS = ("BTCUSDT", "ETHUSDT")
DATA_ROOT = Path("data")
RAW_ROOT = DATA_ROOT / "raw" / "binance_um"
MANIFEST_DIR = DATA_ROOT / "manifests"
REPORT_DIR = DATA_ROOT / "reports"

SCHEMA_VERSION = "tier1_v1"
INGEST_USER_AGENT = "quant-lab-tier1-ingestion/1.0"


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    archive_template: str
    rest_base: str
    rest_kind: str
    expected_interval: str
    expected_interval_ms: int
    normalized_columns: tuple[str, ...]


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_iso() -> str:
    return now_utc().isoformat(timespec="seconds").replace("+00:00", "Z")


def dt_to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def ms_to_iso(ms: int | None) -> str:
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_utc_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def month_floor(value: datetime) -> datetime:
    return datetime(value.year, value.month, 1, tzinfo=UTC)


def add_month(value: datetime) -> datetime:
    if value.month == 12:
        return datetime(value.year + 1, 1, 1, tzinfo=UTC)
    return datetime(value.year, value.month + 1, 1, tzinfo=UTC)


def previous_month_floor(value: datetime) -> datetime:
    current = month_floor(value)
    if current.month == 1:
        return datetime(current.year - 1, 12, 1, tzinfo=UTC)
    return datetime(current.year, current.month - 1, 1, tzinfo=UTC)


def month_iter(start: datetime, end: datetime) -> Iterable[datetime]:
    cursor = month_floor(start)
    end_floor = month_floor(end)
    while cursor <= end_floor:
        yield cursor
        cursor = add_month(cursor)


def archive_url(dataset: Dataset, symbol: str, month: datetime) -> str:
    return dataset.archive_template.format(
        SYMBOL=symbol,
        PAIR=symbol,
        YYYY=f"{month.year:04d}",
        MM=f"{month.month:02d}",
    )


def local_data_path(dataset_id: str, symbol: str, month: datetime) -> Path:
    filename = f"{dataset_id}_{symbol}_{month.year:04d}-{month.month:02d}.csv.gz"
    return RAW_ROOT / dataset_id / f"symbol={symbol}" / filename


def datasets() -> list[Dataset]:
    kline_columns = (
        "timestamp_open_utc",
        "timestamp_close_utc",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume_base",
        "volume_quote",
        "trade_count",
        "taker_buy_base",
        "taker_buy_quote",
        "source",
        "ingested_at_utc",
    )
    price_columns = (
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
    funding_columns = (
        "timestamp_utc",
        "symbol",
        "funding_rate",
        "mark_price_at_funding",
        "source",
        "ingested_at_utc",
    )
    return [
        Dataset(
            "um_klines_1m",
            "https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/klines",
            "symbol_kline",
            "1m",
            60_000,
            kline_columns,
        ),
        Dataset(
            "funding_rate_history",
            "https://data.binance.vision/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/fundingRate",
            "funding",
            "8h_expected",
            28_800_000,
            funding_columns,
        ),
        Dataset(
            "premium_index_klines",
            "https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/premiumIndexKlines",
            "symbol_kline",
            "1m",
            60_000,
            price_columns,
        ),
        Dataset(
            "mark_price_klines",
            "https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/markPriceKlines",
            "symbol_kline",
            "1m",
            60_000,
            price_columns,
        ),
        Dataset(
            "index_price_klines",
            "https://data.binance.vision/data/futures/um/monthly/indexPriceKlines/{PAIR}/1m/{PAIR}-1m-{YYYY}-{MM}.zip",
            "https://fapi.binance.com/fapi/v1/indexPriceKlines",
            "index",
            "1m",
            60_000,
            price_columns,
        ),
    ]


def fetch(url: str, *, method: str = "GET", timeout: float, retries: int = 2) -> tuple[int, bytes, str, int]:
    last_status = 0
    last_error = ""
    for attempt in range(retries + 1):
        req = Request(url, method=method, headers={"User-Agent": INGEST_USER_AGENT})
        try:
            with urlopen(req, timeout=timeout) as response:
                body = b"" if method == "HEAD" else response.read()
                return response.status, body, "", attempt
        except HTTPError as exc:
            last_status = exc.code
            last_error = f"HTTPError: {exc.reason}"
            if exc.code == 404:
                return last_status, b"", last_error, attempt
        except URLError as exc:
            last_status = 0
            last_error = f"URLError: {exc.reason}"
        except Exception as exc:
            last_status = 0
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(0.75 * (2**attempt))
    return last_status, b"", last_error, retries


def status_from_http(status: int, error: str) -> str:
    if status == 200:
        return "OK"
    if status == 404:
        return "NOT_FOUND"
    if status == 0:
        return "ERROR"
    return f"HTTP_{status}"


def checksum_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_archive_row(dataset: Dataset, symbol: str, row: dict[str, str], source_url: str, ingested_at: str) -> dict[str, str]:
    if dataset.dataset_id == "funding_rate_history":
        timestamp_ms = int(row["calc_time"])
        return {
            "timestamp_utc": ms_to_iso(timestamp_ms),
            "symbol": symbol,
            "funding_rate": row["last_funding_rate"],
            "mark_price_at_funding": "",
            "source": source_url,
            "ingested_at_utc": ingested_at,
        }

    open_ms = int(row["open_time"])
    close_ms = int(row["close_time"])
    if dataset.dataset_id == "um_klines_1m":
        return {
            "timestamp_open_utc": ms_to_iso(open_ms),
            "timestamp_close_utc": ms_to_iso(close_ms),
            "symbol": symbol,
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume_base": row["volume"],
            "volume_quote": row["quote_volume"],
            "trade_count": row["count"],
            "taker_buy_base": row["taker_buy_volume"],
            "taker_buy_quote": row["taker_buy_quote_volume"],
            "source": source_url,
            "ingested_at_utc": ingested_at,
        }
    return {
        "timestamp_open_utc": ms_to_iso(open_ms),
        "timestamp_close_utc": ms_to_iso(close_ms),
        "symbol": symbol,
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "source": source_url,
        "ingested_at_utc": ingested_at,
    }


def normalize_rest_row(dataset: Dataset, symbol: str, row: Any, source_url: str, ingested_at: str) -> dict[str, str]:
    if dataset.dataset_id == "funding_rate_history":
        return {
            "timestamp_utc": ms_to_iso(int(row["fundingTime"])),
            "symbol": symbol,
            "funding_rate": str(row["fundingRate"]),
            "mark_price_at_funding": str(row.get("markPrice", "")),
            "source": source_url,
            "ingested_at_utc": ingested_at,
        }

    open_ms = int(row[0])
    close_ms = int(row[6])
    if dataset.dataset_id == "um_klines_1m":
        return {
            "timestamp_open_utc": ms_to_iso(open_ms),
            "timestamp_close_utc": ms_to_iso(close_ms),
            "symbol": symbol,
            "open": str(row[1]),
            "high": str(row[2]),
            "low": str(row[3]),
            "close": str(row[4]),
            "volume_base": str(row[5]),
            "volume_quote": str(row[7]),
            "trade_count": str(row[8]),
            "taker_buy_base": str(row[9]),
            "taker_buy_quote": str(row[10]),
            "source": source_url,
            "ingested_at_utc": ingested_at,
        }
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


def timestamp_ms_from_normalized(dataset: Dataset, row: dict[str, str]) -> int:
    key = "timestamp_utc" if dataset.dataset_id == "funding_rate_history" else "timestamp_open_utc"
    value = row[key].replace("Z", "+00:00")
    return dt_to_ms(datetime.fromisoformat(value))


def schema_fields_for_archive(dataset: Dataset) -> str:
    if dataset.dataset_id == "funding_rate_history":
        return "calc_time,funding_interval_hours,last_funding_rate"
    return "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore"


def schema_fields_for_rest(dataset: Dataset) -> str:
    if dataset.dataset_id == "funding_rate_history":
        return "symbol,fundingRate,fundingTime,markPrice"
    return "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore"


def validate_saved_file(dataset: Dataset, path: Path) -> dict[str, Any]:
    timestamps: list[int] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != dataset.normalized_columns:
            return {
                "row_count": 0,
                "start_ms": None,
                "end_ms": None,
                "expected_rows": 0,
                "missing_rows": 0,
                "duplicate_rows": 0,
                "timestamp_monotonic": False,
                "status": "SCHEMA_FAIL",
                "notes": f"observed_fields={','.join(reader.fieldnames or [])}",
            }
        for row in reader:
            timestamps.append(timestamp_ms_from_normalized(dataset, row))

    duplicates = len(timestamps) - len(set(timestamps))
    monotonic = all(a < b for a, b in zip(timestamps, timestamps[1:]))
    if timestamps:
        unique_sorted = sorted(set(timestamps))
        expected_rows = ((max(unique_sorted) - min(unique_sorted)) // dataset.expected_interval_ms) + 1
        missing_rows = max(0, expected_rows - len(unique_sorted))
        start_ms = min(unique_sorted)
        end_ms = max(unique_sorted)
    else:
        expected_rows = 0
        missing_rows = 0
        start_ms = None
        end_ms = None
    status = "OK" if timestamps and duplicates == 0 and monotonic and missing_rows == 0 else "INTEGRITY_FAIL"
    return {
        "row_count": len(timestamps),
        "start_ms": start_ms,
        "end_ms": end_ms,
        "expected_rows": expected_rows,
        "missing_rows": missing_rows,
        "duplicate_rows": duplicates,
        "timestamp_monotonic": monotonic,
        "status": status,
        "notes": "",
    }


def existing_file_source(path: Path) -> str:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        first = next(reader, None)
        if not first:
            return ""
        return first.get("source", "")


def archive_rows(dataset: Dataset, symbol: str, url: str, body: bytes, ingested_at: str) -> tuple[list[dict[str, str]], str]:
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError("archive contains no CSV")
        with zf.open(csv_names[0]) as raw_handle:
            text = io.TextIOWrapper(raw_handle, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            observed = ",".join(reader.fieldnames or [])
            rows = [normalize_archive_row(dataset, symbol, row, url, ingested_at) for row in reader if row]
    return rows, observed


def rest_url(dataset: Dataset, symbol: str, start_ms: int, end_ms: int) -> str:
    if dataset.rest_kind == "funding":
        params = {"symbol": symbol, "startTime": start_ms, "endTime": end_ms, "limit": 1000}
    elif dataset.rest_kind == "index":
        params = {"pair": symbol, "interval": "1m", "startTime": start_ms, "endTime": end_ms, "limit": 1500}
    else:
        params = {"symbol": symbol, "interval": "1m", "startTime": start_ms, "endTime": end_ms, "limit": 1500}
    return f"{dataset.rest_base}?{urlencode(params)}"


def page_rest_rows(
    dataset: Dataset,
    symbol: str,
    start_ms: int,
    end_ms: int,
    timeout: float,
    retries: int,
    error_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], str, str]:
    rows: list[dict[str, str]] = []
    cursor = start_ms
    first_url = ""
    last_url = ""
    ingested_at = now_iso()
    step_if_empty = dataset.expected_interval_ms
    while cursor <= end_ms:
        request_end = min(end_ms, cursor + dataset.expected_interval_ms * 1499)
        url = rest_url(dataset, symbol, cursor, request_end)
        if not first_url:
            first_url = url
        last_url = url
        status, body, error, retry_count = fetch(url, timeout=timeout, retries=retries)
        if status != 200:
            error_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "source_url": url,
                    "error_type": status_from_http(status, error),
                    "error_message": error,
                    "occurred_at_utc": now_iso(),
                    "retry_count": retry_count,
                    "status": "FAILED",
                }
            )
            break
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, list) or not payload:
            cursor += step_if_empty
            if dataset.rest_kind != "funding":
                break
            continue
        normalized = [normalize_rest_row(dataset, symbol, item, url, ingested_at) for item in payload]
        rows.extend(normalized)
        last_ts = timestamp_ms_from_normalized(dataset, normalized[-1])
        next_cursor = last_ts + dataset.expected_interval_ms
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        if len(payload) < (1000 if dataset.rest_kind == "funding" else 1500):
            break
        time.sleep(0.04)
    source_url = first_url if first_url == last_url else f"{first_url} ... {last_url}"
    return rows, source_url, schema_fields_for_rest(dataset)


def save_normalized(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def ingest_one(
    dataset: Dataset,
    symbol: str,
    month: datetime,
    start_ms: int,
    end_ms: int,
    timeout: float,
    retries: int,
    force: bool,
    error_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    output_path = local_data_path(dataset.dataset_id, symbol, month)
    reuse_existing = output_path.exists() and not force and month < previous_month_floor(now_utc())
    if reuse_existing:
        validation = validate_saved_file(dataset, output_path)
        source_type = "existing"
        source_url = existing_file_source(output_path)
        observed_schema = ",".join(dataset.normalized_columns)
        notes = "existing file reused"
    else:
        url = archive_url(dataset, symbol, month)
        source_type = "archive"
        source_url = url
        observed_schema = schema_fields_for_archive(dataset)
        notes = ""
        status, body, error, retry_count = fetch(url, timeout=timeout, retries=retries)
        if status == 200:
            try:
                rows, observed_schema = archive_rows(dataset, symbol, url, body, now_iso())
                rows = [row for row in rows if start_ms <= timestamp_ms_from_normalized(dataset, row) <= end_ms]
                save_normalized(output_path, dataset.normalized_columns, rows)
            except Exception as exc:
                error_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": url,
                        "error_type": "ARCHIVE_PARSE_ERROR",
                        "error_message": f"{type(exc).__name__}: {exc}",
                        "occurred_at_utc": now_iso(),
                        "retry_count": retry_count,
                        "status": "FAILED",
                    }
                )
        else:
            fallback_floor = previous_month_floor(now_utc())
            if month < fallback_floor:
                source_type = "archive_missing"
                observed_schema = schema_fields_for_archive(dataset)
                notes = "archive unavailable outside newest REST fallback period"
                error_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": url,
                        "error_type": status_from_http(status, error),
                        "error_message": error or "archive not found outside newest fallback period",
                        "occurred_at_utc": now_iso(),
                        "retry_count": retry_count,
                        "status": "FAILED",
                    }
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                save_normalized(output_path, dataset.normalized_columns, [])
                validation = validate_saved_file(dataset, output_path)
                file_size, file_sha = checksum_file(output_path)
                return {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "source_type": source_type,
                    "source_url": url,
                    "local_path": str(output_path.as_posix()),
                    "start_timestamp_utc": ms_to_iso(validation["start_ms"]),
                    "end_timestamp_utc": ms_to_iso(validation["end_ms"]),
                    "row_count": validation["row_count"],
                    "expected_interval": dataset.expected_interval,
                    "schema_version": SCHEMA_VERSION,
                    "observed_schema_fields": observed_schema,
                    "status": validation["status"],
                    "notes": notes,
                    "_gap": {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "window_start_utc": ms_to_iso(start_ms),
                        "window_end_utc": ms_to_iso(end_ms),
                        "expected_interval": dataset.expected_interval,
                        "expected_rows": validation["expected_rows"],
                        "observed_rows": validation["row_count"],
                        "missing_rows": validation["missing_rows"],
                        "duplicate_rows": validation["duplicate_rows"],
                        "timestamp_monotonic": str(validation["timestamp_monotonic"]).upper(),
                        "status": validation["status"],
                        "notes": notes,
                    },
                    "_checksum": {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "local_path": str(output_path.as_posix()),
                        "source_url": url,
                        "bytes": file_size,
                        "sha256": file_sha,
                        "created_at_utc": now_iso(),
                        "notes": validation["status"],
                    },
                }

            source_type = "rest_fallback"
            if status != 404:
                error_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "source_url": url,
                        "error_type": status_from_http(status, error),
                        "error_message": error,
                        "occurred_at_utc": now_iso(),
                        "retry_count": retry_count,
                        "status": "FAILED",
                    }
                )
            rows, source_url, observed_schema = page_rest_rows(dataset, symbol, start_ms, end_ms, timeout, retries, error_rows)
            if rows:
                save_normalized(output_path, dataset.normalized_columns, rows)
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                save_normalized(output_path, dataset.normalized_columns, [])
                notes = f"{notes}; no rows from REST fallback".strip("; ")
        validation = validate_saved_file(dataset, output_path)

    file_size, file_sha = checksum_file(output_path)
    row_status = validation["status"]
    if validation["status"] != "OK":
        notes = f"{notes}; integrity={validation['status']} {validation['notes']}".strip("; ")
    return {
        "dataset_id": dataset.dataset_id,
        "symbol": symbol,
        "source_type": source_type,
        "source_url": source_url,
        "local_path": str(output_path.as_posix()),
        "start_timestamp_utc": ms_to_iso(validation["start_ms"]),
        "end_timestamp_utc": ms_to_iso(validation["end_ms"]),
        "row_count": validation["row_count"],
        "expected_interval": dataset.expected_interval,
        "schema_version": SCHEMA_VERSION,
        "observed_schema_fields": observed_schema,
        "status": row_status,
        "notes": notes,
        "_gap": {
            "dataset_id": dataset.dataset_id,
            "symbol": symbol,
            "window_start_utc": ms_to_iso(start_ms),
            "window_end_utc": ms_to_iso(end_ms),
            "expected_interval": dataset.expected_interval,
            "expected_rows": validation["expected_rows"],
            "observed_rows": validation["row_count"],
            "missing_rows": validation["missing_rows"],
            "duplicate_rows": validation["duplicate_rows"],
            "timestamp_monotonic": str(validation["timestamp_monotonic"]).upper(),
            "status": row_status,
            "notes": notes,
        },
        "_checksum": {
            "dataset_id": dataset.dataset_id,
            "symbol": symbol,
            "local_path": str(output_path.as_posix()),
            "source_url": source_url,
            "bytes": file_size,
            "sha256": file_sha,
            "created_at_utc": now_iso(),
            "notes": row_status,
        },
    }


def month_bounds(month: datetime, start: datetime, end: datetime) -> tuple[int, int]:
    window_start = max(month, start)
    window_end_dt = min(add_month(month), end)
    return dt_to_ms(window_start), dt_to_ms(window_end_dt) - 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest approved Binance USD-M TIER 1 raw datasets.")
    parser.add_argument("--start-date", default="2024-01-01", help="UTC start date, inclusive, YYYY-MM-DD.")
    parser.add_argument("--end-date", default="", help="UTC end date, exclusive, YYYY-MM-DD. Defaults to now.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--force", action="store_true", help="Re-download and overwrite existing normalized files.")
    args = parser.parse_args()

    start = parse_utc_date(args.start_date)
    end = parse_utc_date(args.end_date) if args.end_date else now_utc()
    if end <= start:
        raise SystemExit("--end-date must be after --start-date")

    manifest_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    checksum_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for dataset in datasets():
        for symbol in SYMBOLS:
            for month in month_iter(start, end):
                start_ms, end_ms = month_bounds(month, start, end)
                if end_ms < start_ms:
                    continue
                print(f"ingest {dataset.dataset_id} {symbol} {month.year:04d}-{month.month:02d}", flush=True)
                row = ingest_one(dataset, symbol, month, start_ms, end_ms, args.timeout, args.retries, args.force, error_rows)
                gap_rows.append(row.pop("_gap"))
                checksum_rows.append(row.pop("_checksum"))
                manifest_rows.append(row)

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
    error_fields = [
        "dataset_id",
        "symbol",
        "source_url",
        "error_type",
        "error_message",
        "occurred_at_utc",
        "retry_count",
        "status",
    ]
    write_csv(MANIFEST_DIR / "tier1_manifest.csv", manifest_fields, manifest_rows)
    write_csv(REPORT_DIR / "tier1_gaps_report.csv", gap_fields, gap_rows)
    write_csv(MANIFEST_DIR / "tier1_checksums.csv", checksum_fields, checksum_rows)
    write_csv(REPORT_DIR / "tier1_ingestion_errors.csv", error_fields, error_rows)

    bad_rows = [row for row in manifest_rows if row["status"] != "OK"]
    summary = {
        "manifest_rows": len(manifest_rows),
        "error_rows": len(error_rows),
        "non_ok_manifest_rows": len(bad_rows),
        "status": "PASS" if not bad_rows and not error_rows else "PARTIAL_OR_FAILED",
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
