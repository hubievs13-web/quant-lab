"""Binance OI + LSR + taker-ratio ingestor (Phase 2).

Source: daily `metrics` zip on `data.binance.vision` at 5-minute
granularity. CSV columns:

    create_time, symbol, sum_open_interest, sum_open_interest_value,
    count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
    count_long_short_ratio, sum_taker_long_short_vol_ratio
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

BASE = "https://data.binance.vision/data/futures/um/daily/metrics"


def url_for(symbol: str, day: dt.date) -> str:
    return f"{BASE}/{symbol}/{symbol}-metrics-{day}.zip"


def _parse_human_ts_to_ms(s: str) -> int:
    t = dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.UTC)
    return int(t.timestamp() * 1000)


def parse_metrics_csv(rows: list[list[str]], symbol: str) -> pa.Table:
    if rows and rows[0] and rows[0][0] == "create_time":
        rows = rows[1:]
    ts: list[int] = []
    oi_base: list[float] = []
    oi_q: list[float] = []
    lsr_top_acc: list[float] = []
    lsr_top_pos: list[float] = []
    lsr_account: list[float] = []
    taker_ratio: list[float] = []
    for row in rows:
        if not row or len(row) < 8:
            continue
        ts.append(_parse_human_ts_to_ms(row[0]))
        oi_base.append(float(row[2]))
        oi_q.append(float(row[3]))
        lsr_top_acc.append(float(row[4]))
        lsr_top_pos.append(float(row[5]))
        lsr_account.append(float(row[6]))
        taker_ratio.append(float(row[7]))
    n = len(ts)
    return pa.Table.from_arrays(
        [
            pa.array(ts, pa.int64()),
            pa.array(oi_base, pa.float64()),
            pa.array(oi_q, pa.float64()),
            pa.array(lsr_account, pa.float64()),
            pa.array(lsr_top_acc, pa.float64()),
            pa.array(lsr_top_pos, pa.float64()),
            pa.array(taker_ratio, pa.float64()),
            pa.array(["binance"] * n),
            pa.array([symbol] * n),
        ],
        schema=pa.schema(
            [
                ("ts_ms", pa.int64()),
                ("oi_base", pa.float64()),
                ("oi_value_quote", pa.float64()),
                ("long_short_account_ratio", pa.float64()),
                ("top_trader_account_ratio", pa.float64()),
                ("top_trader_position_ratio", pa.float64()),
                ("taker_long_short_vol_ratio", pa.float64()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
            ]
        ),
    )


def fetch_day(symbol: str, day: dt.date, store_root: Path) -> tuple[Path | None, int]:
    payload = http_get_bytes(url_for(symbol, day), accept_404_as_none=True)
    if payload is None:
        return None, 0
    rows = csv_rows_from_zip(payload)
    table = parse_metrics_csv(rows, symbol)
    out = store_root / "raw/binance/oi" / symbol / f"{symbol}-metrics-{day}.parquet"
    write_parquet_atomic(table, out)
    return out, table.num_rows


def fetch_range(
    symbol: str, end_inclusive: dt.date, n_days: int, store_root: Path
) -> list[tuple[dt.date, Path | None, int]]:
    start = end_inclusive - dt.timedelta(days=n_days - 1)
    return [(d, *fetch_day(symbol, d, store_root)) for d in daterange(start, end_inclusive)]
