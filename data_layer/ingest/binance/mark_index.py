"""Binance USD-M futures mark / index price klines ingestor.

Source: `data.binance.vision` daily zip archives:
- markPriceKlines/<symbol>/<interval>/<symbol>-<interval>-<date>.zip
- indexPriceKlines/<symbol>/<interval>/<symbol>-<interval>-<date>.zip

CSV column layout matches the OHLCV klines (12 fields). For mark and
index series, only `open / high / low / close` are meaningful; volume
fields are 0. We persist `close` as `mark_close` / `index_close` and
keep `ts_open_ms`, `ts_close_ms` for joining.

Doc: https://github.com/binance/binance-public-data
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pyarrow as pa

from data_layer.ingest.common import (
    csv_rows_from_zip,
    daterange,
    http_get_bytes,
    write_parquet_atomic,
)

BASE_MARK = "https://data.binance.vision/data/futures/um/daily/markPriceKlines"
BASE_INDEX = "https://data.binance.vision/data/futures/um/daily/indexPriceKlines"


def url_mark(symbol: str, interval: str, day: dt.date) -> str:
    return f"{BASE_MARK}/{symbol}/{interval}/{symbol}-{interval}-{day}.zip"


def url_index(symbol: str, interval: str, day: dt.date) -> str:
    return f"{BASE_INDEX}/{symbol}/{interval}/{symbol}-{interval}-{day}.zip"


def _parse_klines(rows: list[list[str]], close_col: str, symbol: str, tf: str) -> pa.Table:
    if rows and rows[0] and rows[0][0] == "open_time":
        rows = rows[1:]
    ts_open: list[int] = []
    ts_close: list[int] = []
    closes: list[float] = []
    for row in rows:
        if not row or len(row) < 7:
            continue
        ts_open.append(int(row[0]))
        ts_close.append(int(row[6]))
        closes.append(float(row[4]))
    n = len(ts_open)
    return pa.Table.from_arrays(
        [
            pa.array(ts_open, pa.int64()),
            pa.array(ts_close, pa.int64()),
            pa.array(closes, pa.float64()),
            pa.array(["binance"] * n),
            pa.array([symbol] * n),
            pa.array([tf] * n),
        ],
        schema=pa.schema(
            [
                ("ts_open_ms", pa.int64()),
                ("ts_close_ms", pa.int64()),
                (close_col, pa.float64()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
                ("timeframe", pa.string()),
            ]
        ),
    )


def fetch_mark_day(
    symbol: str, interval: str, day: dt.date, store_root: Path
) -> tuple[Path | None, int]:
    payload = http_get_bytes(url_mark(symbol, interval, day), accept_404_as_none=True)
    if payload is None:
        return None, 0
    rows = csv_rows_from_zip(payload)
    table = _parse_klines(rows, "mark_close", symbol, interval)
    out = (
        store_root / "raw/binance/mark" / symbol / interval
        / f"{symbol}-{interval}-{day}.parquet"
    )
    write_parquet_atomic(table, out)
    return out, table.num_rows


def fetch_index_day(
    symbol: str, interval: str, day: dt.date, store_root: Path
) -> tuple[Path | None, int]:
    payload = http_get_bytes(url_index(symbol, interval, day), accept_404_as_none=True)
    if payload is None:
        return None, 0
    rows = csv_rows_from_zip(payload)
    table = _parse_klines(rows, "index_close", symbol, interval)
    out = (
        store_root / "raw/binance/index" / symbol / interval
        / f"{symbol}-{interval}-{day}.parquet"
    )
    write_parquet_atomic(table, out)
    return out, table.num_rows


def fetch_range(
    symbol: str,
    interval: str,
    end_inclusive: dt.date,
    n_days: int,
    store_root: Path,
) -> tuple[list[tuple[dt.date, Path | None, int]], list[tuple[dt.date, Path | None, int]]]:
    """Fetch mark + index daily klines over [end - n_days + 1 ... end]."""
    start = end_inclusive - dt.timedelta(days=n_days - 1)
    days = daterange(start, end_inclusive)
    mark_out = [(d, *fetch_mark_day(symbol, interval, d, store_root)) for d in days]
    index_out = [(d, *fetch_index_day(symbol, interval, d, store_root)) for d in days]
    return mark_out, index_out
