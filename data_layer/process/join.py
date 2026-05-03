"""Left-join derivatives onto the OHLCV bar grid.

Joins funding (forward-filled within `funding_interval_ms`) and OI
(forward-filled with TTL of 60 minutes) onto the canonical bars.
Mark and index price klines are joined exactly on `ts_open_ms` when
available; from those we derive `basis_bp = (mark - index)/index*1e4`.
Liquidations and book snapshots remain deferred.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

OI_TTL_MS = 60 * 60 * 1000


def _read_parquet_dir(d: Path) -> pd.DataFrame:
    if not d.exists():
        return pd.DataFrame()
    files = sorted(d.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pq.read_table(p).to_pandas() for p in files], ignore_index=True)


def join_for(symbol: str, timeframe: str, store_root: Path) -> tuple[Path | None, int]:
    bars_path = store_root / "processed/bars/binance" / symbol / f"{timeframe}.parquet"
    if not bars_path.exists():
        return None, 0
    bars = (
        pq.read_table(bars_path).to_pandas().sort_values("ts_open_ms").reset_index(drop=True)
    )

    funding = _read_parquet_dir(store_root / "raw/binance/funding" / symbol)
    if not funding.empty:
        funding = funding.sort_values("ts_settle_ms").reset_index(drop=True)
        f = funding[["ts_settle_ms", "funding_rate", "funding_interval_ms"]].rename(
            columns={"ts_settle_ms": "ts_match"}
        )
        m = pd.merge_asof(
            bars[["ts_open_ms"]],
            f,
            left_on="ts_open_ms",
            right_on="ts_match",
            direction="backward",
        )
        valid = (m["ts_open_ms"] - m["ts_match"]) <= m["funding_interval_ms"].fillna(0)
        bars["funding_rate_ffill"] = m["funding_rate"].where(valid)
        bars["funding_minutes_to_next"] = (
            (m["ts_match"] + m["funding_interval_ms"] - m["ts_open_ms"]) / 60000.0
        )
    else:
        bars["funding_rate_ffill"] = pd.NA
        bars["funding_minutes_to_next"] = pd.NA

    oi = _read_parquet_dir(store_root / "raw/binance/oi" / symbol)
    if not oi.empty:
        oi = oi.sort_values("ts_ms").reset_index(drop=True)
        o = oi[["ts_ms", "oi_base", "oi_value_quote"]].rename(columns={"ts_ms": "ts_match"})
        m = pd.merge_asof(
            bars[["ts_open_ms"]],
            o,
            left_on="ts_open_ms",
            right_on="ts_match",
            direction="backward",
        )
        too_old = (m["ts_open_ms"] - m["ts_match"]) > OI_TTL_MS
        bars["oi_base"] = m["oi_base"].where(~too_old)
        bars["oi_value_quote"] = m["oi_value_quote"].where(~too_old)
    else:
        bars["oi_base"] = pd.NA
        bars["oi_value_quote"] = pd.NA

    mark = _read_parquet_dir(store_root / "raw/binance/mark" / symbol / timeframe)
    if not mark.empty:
        mk = mark[["ts_open_ms", "mark_close"]].drop_duplicates(
            subset=["ts_open_ms"], keep="first"
        )
        bars = bars.merge(mk, on="ts_open_ms", how="left")
    else:
        bars["mark_close"] = pd.NA

    index = _read_parquet_dir(store_root / "raw/binance/index" / symbol / timeframe)
    if not index.empty:
        ix = index[["ts_open_ms", "index_close"]].drop_duplicates(
            subset=["ts_open_ms"], keep="first"
        )
        bars = bars.merge(ix, on="ts_open_ms", how="left")
    else:
        bars["index_close"] = pd.NA

    out_path = (
        store_root / "processed/bars_joined/binance" / symbol / f"{timeframe}.parquet"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pandas(bars, preserve_index=False), out_path, compression="snappy"
    )
    return out_path, len(bars)
