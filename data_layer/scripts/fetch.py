"""Binance validation fetcher.

Targets: Binance BTCUSDT / ETHUSDT.
- OHLCV 5m for the last 365 complete UTC days
- OHLCV 1h for the last 365 complete UTC days
- Mark / index price klines (5m and 1h for 365d)
- Funding rate (monthly zips covering the last 365 complete UTC days)
- OI / metrics 5-minute history for the last 365 complete UTC days

All bulk data is written under `data_layer/store/` which is gitignored.

Window widened from 90/180/30 to 365 days uniformly so the cross-symbol
Pareto evidence gate from `obsidian/01_Rules/02_Fee_Slippage_Model.md`
and `pre_backtest_auditor_prompt.md` has enough samples (n>=80) to give
meaningful verdicts. See `data_layer/config/universe.yaml`.
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
SYMBOLS = ("BTCUSDT", "ETHUSDT")


# Default validation windows (overridable for unit tests / smoke).
# Values must stay in sync with `data_layer/config/universe.yaml`
# `history_window` keys for documentation purposes.
DAYS_5M = 1095
DAYS_1H = 1095
DAYS_FUNDING = 1095
# Binance Vision OI 5m archive only covers the recent ~30 days; for
# anything beyond that the ingest layer downgrades to 1h granularity.
# Keep the budget capped to 365 to avoid surprises at the 5m level
# and to bound fetch time.
DAYS_OI = 365


def fetch_binance_symbol(
    symbol: str,
    days_5m: int = DAYS_5M,
    days_1h: int = DAYS_1H,
    days_funding: int = DAYS_FUNDING,
    days_oi: int = DAYS_OI,
) -> int:
    end_inclusive = utc_today() - dt.timedelta(days=1)
    print(f"[fetch] {symbol} window end (inclusive UTC): {end_inclusive}")

    print(f"[fetch] {symbol} OHLCV 5m, {days_5m} days")
    out_5m = binance_ohlcv.fetch_range(symbol, "5m", end_inclusive, days_5m, STORE_ROOT)
    n_5m = sum(n for _, _, n in out_5m)
    print(f"  rows={n_5m} files={sum(1 for _, p, _ in out_5m if p is not None)}")

    print(f"[fetch] {symbol} OHLCV 1h, {days_1h} days")
    out_1h = binance_ohlcv.fetch_range(symbol, "1h", end_inclusive, days_1h, STORE_ROOT)
    n_1h = sum(n for _, _, n in out_1h)
    print(f"  rows={n_1h} files={sum(1 for _, p, _ in out_1h if p is not None)}")

    for tf, n_days in (("5m", days_5m), ("1h", days_1h)):
        print(f"[fetch] {symbol} mark+index {tf}, {n_days} days")
        mark_out, index_out = binance_mark_index.fetch_range(
            symbol, tf, end_inclusive, n_days, STORE_ROOT
        )
        n_m = sum(n for _, _, n in mark_out)
        n_i = sum(n for _, _, n in index_out)
        f_m = sum(1 for _, p, _ in mark_out if p is not None)
        f_i = sum(1 for _, p, _ in index_out if p is not None)
        print(f"  mark rows={n_m} files={f_m} | index rows={n_i} files={f_i}")

    print(f"[fetch] {symbol} funding (monthly zips covering last {days_funding} days)")
    out_f = binance_funding.fetch_smoke(symbol, end_inclusive, days_funding, STORE_ROOT)
    n_f = sum(n for _, _, n in out_f)
    print(f"  rows={n_f} months={sum(1 for _, p, _ in out_f if p is not None)}")

    print(f"[fetch] {symbol} OI / metrics, {days_oi} days")
    out_oi = binance_oi.fetch_range(symbol, end_inclusive, days_oi, STORE_ROOT)
    n_oi = sum(n for _, _, n in out_oi)
    print(f"  rows={n_oi} files={sum(1 for _, p, _ in out_oi if p is not None)}")
    return 0


def fetch_binance_smoke(
    days_5m: int = DAYS_5M,
    days_1h: int = DAYS_1H,
    days_funding: int = DAYS_FUNDING,
    days_oi: int = DAYS_OI,
) -> int:
    fetch_binance_symbol(
        "BTCUSDT",
        days_5m=days_5m,
        days_1h=days_1h,
        days_funding=days_funding,
        days_oi=days_oi,
    )
    print("[fetch] done.")
    return 0


def fetch_binance_validation(
    symbols: tuple[str, ...] = SYMBOLS,
    days_5m: int = DAYS_5M,
    days_1h: int = DAYS_1H,
    days_funding: int = DAYS_FUNDING,
    days_oi: int = DAYS_OI,
) -> int:
    for symbol in symbols:
        fetch_binance_symbol(
            symbol,
            days_5m=days_5m,
            days_1h=days_1h,
            days_funding=days_funding,
            days_oi=days_oi,
        )
    print("[fetch] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(fetch_binance_smoke())
