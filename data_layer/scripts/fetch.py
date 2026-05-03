"""Binance smoke fetcher.

Targets: BTCUSDT only.
- OHLCV 5m for the last 90 complete UTC days
- OHLCV 1h for the last 180 complete UTC days
- Mark / index price klines (5m for 90d, 1h for 180d)
- Funding rate (monthly zips covering the last 180 complete UTC days)
- OI / metrics 5-minute history for the last 30 complete UTC days

All bulk data is written under `data_layer/store/` which is gitignored.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from data_layer.ingest.binance import (
    funding as binance_funding,
    mark_index as binance_mark_index,
    ohlcv as binance_ohlcv,
    open_interest as binance_oi,
)
from data_layer.ingest.common import utc_today

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
SYMBOL = "BTCUSDT"


# Default smoke windows (overridable for unit tests).
DAYS_5M = 90
DAYS_1H = 180
DAYS_FUNDING = 180
DAYS_OI = 30


def fetch_binance_smoke(
    days_5m: int = DAYS_5M,
    days_1h: int = DAYS_1H,
    days_funding: int = DAYS_FUNDING,
    days_oi: int = DAYS_OI,
) -> int:
    end_inclusive = utc_today() - dt.timedelta(days=1)
    print(f"[fetch] window end (inclusive UTC): {end_inclusive}")

    print(f"[fetch] OHLCV 5m, {days_5m} days")
    out_5m = binance_ohlcv.fetch_range(SYMBOL, "5m", end_inclusive, days_5m, STORE_ROOT)
    n_5m = sum(n for _, _, n in out_5m)
    print(f"  rows={n_5m} files={sum(1 for _, p, _ in out_5m if p is not None)}")

    print(f"[fetch] OHLCV 1h, {days_1h} days")
    out_1h = binance_ohlcv.fetch_range(SYMBOL, "1h", end_inclusive, days_1h, STORE_ROOT)
    n_1h = sum(n for _, _, n in out_1h)
    print(f"  rows={n_1h} files={sum(1 for _, p, _ in out_1h if p is not None)}")

    for tf, n_days in (("5m", days_5m), ("1h", days_1h)):
        print(f"[fetch] mark+index {tf}, {n_days} days")
        mark_out, index_out = binance_mark_index.fetch_range(
            SYMBOL, tf, end_inclusive, n_days, STORE_ROOT
        )
        n_m = sum(n for _, _, n in mark_out)
        n_i = sum(n for _, _, n in index_out)
        f_m = sum(1 for _, p, _ in mark_out if p is not None)
        f_i = sum(1 for _, p, _ in index_out if p is not None)
        print(f"  mark rows={n_m} files={f_m} | index rows={n_i} files={f_i}")

    print(f"[fetch] funding (monthly zips covering last {days_funding} days)")
    out_f = binance_funding.fetch_smoke(SYMBOL, end_inclusive, days_funding, STORE_ROOT)
    n_f = sum(n for _, _, n in out_f)
    print(f"  rows={n_f} months={sum(1 for _, p, _ in out_f if p is not None)}")

    print(f"[fetch] OI / metrics, {days_oi} days")
    out_oi = binance_oi.fetch_range(SYMBOL, end_inclusive, days_oi, STORE_ROOT)
    n_oi = sum(n for _, _, n in out_oi)
    print(f"  rows={n_oi} files={sum(1 for _, p, _ in out_oi if p is not None)}")

    print("[fetch] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(fetch_binance_smoke())
