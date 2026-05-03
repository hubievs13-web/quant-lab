"""Phase 2 smoke fetcher.

Targets: BTCUSDT only.
- OHLCV 5m for the last 7 complete UTC days
- OHLCV 1h for the last 30 complete UTC days
- Funding rate (monthly zips covering the last 30 complete UTC days)
- OI / metrics 5-minute history for the last 7 complete UTC days

All bulk data is written under `data_layer/store/` which is gitignored.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from data_layer.ingest.binance import (
    funding as binance_funding,
    ohlcv as binance_ohlcv,
    open_interest as binance_oi,
)
from data_layer.ingest.common import utc_today

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
SYMBOL = "BTCUSDT"


def fetch_binance_smoke() -> int:
    end_inclusive = utc_today() - dt.timedelta(days=1)
    print(f"[fetch] window end (inclusive UTC): {end_inclusive}")

    print("[fetch] OHLCV 5m, 7 days")
    out_5m = binance_ohlcv.fetch_range(SYMBOL, "5m", end_inclusive, 7, STORE_ROOT)
    n_5m = sum(n for _, _, n in out_5m)
    print(f"  rows={n_5m} files={sum(1 for _, p, _ in out_5m if p is not None)}")

    print("[fetch] OHLCV 1h, 30 days")
    out_1h = binance_ohlcv.fetch_range(SYMBOL, "1h", end_inclusive, 30, STORE_ROOT)
    n_1h = sum(n for _, _, n in out_1h)
    print(f"  rows={n_1h} files={sum(1 for _, p, _ in out_1h if p is not None)}")

    print("[fetch] funding (monthly zips covering last 30 days)")
    out_f = binance_funding.fetch_smoke(SYMBOL, end_inclusive, 30, STORE_ROOT)
    n_f = sum(n for _, _, n in out_f)
    print(f"  rows={n_f} months={sum(1 for _, p, _ in out_f if p is not None)}")

    print("[fetch] OI / metrics, 7 days")
    out_oi = binance_oi.fetch_range(SYMBOL, end_inclusive, 7, STORE_ROOT)
    n_oi = sum(n for _, _, n in out_oi)
    print(f"  rows={n_oi} files={sum(1 for _, p, _ in out_oi if p is not None)}")

    print("[fetch] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(fetch_binance_smoke())
