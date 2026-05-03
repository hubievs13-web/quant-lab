"""Binance funding rate ingestor (Phase 2).

Source: monthly zip per symbol on `data.binance.vision`.
CSV columns: calc_time (epoch ms), funding_interval_hours, last_funding_rate.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pyarrow as pa

from data_layer.ingest.common import (
    csv_rows_from_zip,
    http_get_bytes,
    write_parquet_atomic,
)

BASE = "https://data.binance.vision/data/futures/um/monthly/fundingRate"


def url_for(symbol: str, year: int, month: int) -> str:
    return f"{BASE}/{symbol}/{symbol}-fundingRate-{year:04d}-{month:02d}.zip"


def parse_funding_csv(rows: list[list[str]], symbol: str) -> pa.Table:
    if rows and rows[0] and rows[0][0] == "calc_time":
        rows = rows[1:]
    ts: list[int] = []
    interval_ms: list[int] = []
    rate: list[float] = []
    for row in rows:
        if not row or len(row) < 3:
            continue
        ts.append(int(row[0]))
        interval_ms.append(int(float(row[1])) * 3600 * 1000)
        rate.append(float(row[2]))
    n = len(ts)
    return pa.Table.from_arrays(
        [
            pa.array(ts, pa.int64()),
            pa.array(rate, pa.float64()),
            pa.array(interval_ms, pa.int64()),
            pa.array([None] * n, pa.float64()),  # predicted_funding_rate (n/a in CDN)
            pa.array(["binance"] * n),
            pa.array([symbol] * n),
        ],
        schema=pa.schema(
            [
                ("ts_settle_ms", pa.int64()),
                ("funding_rate", pa.float64()),
                ("funding_interval_ms", pa.int64()),
                ("predicted_funding_rate", pa.float64()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
            ]
        ),
    )


def fetch_month(symbol: str, year: int, month: int, store_root: Path) -> tuple[Path | None, int]:
    payload = http_get_bytes(url_for(symbol, year, month), accept_404_as_none=True)
    if payload is None:
        return None, 0
    rows = csv_rows_from_zip(payload)
    table = parse_funding_csv(rows, symbol)
    out = (
        store_root / "raw/binance/funding" / symbol /
        f"{symbol}-fundingRate-{year:04d}-{month:02d}.parquet"
    )
    write_parquet_atomic(table, out)
    return out, table.num_rows


def fetch_smoke(
    symbol: str, end_inclusive: dt.date, n_days: int, store_root: Path
) -> list[tuple[str, Path | None, int]]:
    """Fetch the months covering [end - n_days + 1 ... end]."""
    start = end_inclusive - dt.timedelta(days=n_days - 1)
    months: set[tuple[int, int]] = set()
    cur = start.replace(day=1)
    while cur <= end_inclusive:
        months.add((cur.year, cur.month))
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return [
        (f"{y:04d}-{m:02d}", *fetch_month(symbol, y, m, store_root))
        for y, m in sorted(months)
    ]
