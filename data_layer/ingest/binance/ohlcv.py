"""Binance USD-M futures OHLCV ingestor (Phase 2).

Source: `data.binance.vision` public CDN (daily zip per symbol+interval).
The Binance fapi REST endpoints are geoblocked from many regions; the
CDN is the documented archive that mirrors the same data with no key.
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

BASE = "https://data.binance.vision/data/futures/um/daily/klines"

# Source CSV columns (12):
# open_time, open, high, low, close, volume, close_time, quote_volume,
# count, taker_buy_volume, taker_buy_quote_volume, ignore


def url_for(symbol: str, interval: str, day: dt.date) -> str:
    return f"{BASE}/{symbol}/{interval}/{symbol}-{interval}-{day}.zip"


def parse_klines_csv(rows: list[list[str]], symbol: str, timeframe: str) -> pa.Table:
    if rows and rows[0] and rows[0][0] == "open_time":
        rows = rows[1:]
    cols: dict[str, list] = {
        "ts_open_ms": [],
        "ts_close_ms": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume_base": [],
        "volume_quote": [],
        "trades": [],
        "taker_buy_base": [],
        "taker_buy_quote": [],
    }
    for row in rows:
        if not row or len(row) < 12:
            continue
        cols["ts_open_ms"].append(int(row[0]))
        cols["ts_close_ms"].append(int(row[6]))
        cols["open"].append(float(row[1]))
        cols["high"].append(float(row[2]))
        cols["low"].append(float(row[3]))
        cols["close"].append(float(row[4]))
        cols["volume_base"].append(float(row[5]))
        cols["volume_quote"].append(float(row[7]))
        cols["trades"].append(int(row[8]))
        cols["taker_buy_base"].append(float(row[9]))
        cols["taker_buy_quote"].append(float(row[10]))
    n = len(cols["ts_open_ms"])
    arrays = [
        pa.array(cols["ts_open_ms"], pa.int64()),
        pa.array(cols["ts_close_ms"], pa.int64()),
        pa.array(cols["open"], pa.float64()),
        pa.array(cols["high"], pa.float64()),
        pa.array(cols["low"], pa.float64()),
        pa.array(cols["close"], pa.float64()),
        pa.array(cols["volume_base"], pa.float64()),
        pa.array(cols["volume_quote"], pa.float64()),
        pa.array(cols["trades"], pa.int64()),
        pa.array(cols["taker_buy_base"], pa.float64()),
        pa.array(cols["taker_buy_quote"], pa.float64()),
        pa.array(["binance"] * n),
        pa.array([symbol] * n),
        pa.array([timeframe] * n),
    ]
    schema = pa.schema(
        [
            ("ts_open_ms", pa.int64()),
            ("ts_close_ms", pa.int64()),
            ("open", pa.float64()),
            ("high", pa.float64()),
            ("low", pa.float64()),
            ("close", pa.float64()),
            ("volume_base", pa.float64()),
            ("volume_quote", pa.float64()),
            ("trades", pa.int64()),
            ("taker_buy_base", pa.float64()),
            ("taker_buy_quote", pa.float64()),
            ("exchange", pa.string()),
            ("symbol", pa.string()),
            ("timeframe", pa.string()),
        ]
    )
    return pa.Table.from_arrays(arrays, schema=schema)


def fetch_day(symbol: str, interval: str, day: dt.date, store_root: Path) -> tuple[Path | None, int]:
    """Return (parquet_path or None, row_count). None on upstream 404."""
    payload = http_get_bytes(url_for(symbol, interval, day), accept_404_as_none=True)
    if payload is None:
        return None, 0
    rows = csv_rows_from_zip(payload)
    table = parse_klines_csv(rows, symbol, interval)
    out = store_root / "raw/binance/ohlcv" / symbol / interval / f"{symbol}-{interval}-{day}.parquet"
    write_parquet_atomic(table, out)
    return out, table.num_rows


def fetch_range(
    symbol: str,
    interval: str,
    end_inclusive: dt.date,
    n_days: int,
    store_root: Path,
) -> list[tuple[dt.date, Path | None, int]]:
    start = end_inclusive - dt.timedelta(days=n_days - 1)
    return [(d, *fetch_day(symbol, interval, d, store_root)) for d in daterange(start, end_inclusive)]
