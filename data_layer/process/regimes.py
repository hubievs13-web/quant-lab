"""Regime label engine for the Market Research Data Layer (Phase 3).

Reads `processed/features/binance/<SYMBOL>/<TF>.parquet` and writes
`processed/regimes/binance/<SYMBOL>/<TF>.parquet` with per-bar regime
labels. Anti-lookahead: every label for bar `i` is a function of
features at bar `i` (which were themselves computed without future
bars). No shifts of negative offset are used.

Threshold parameters live in `data_layer/config/regimes.yaml`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from data_layer.ingest.common import write_parquet_atomic

BARS_PER_DAY = {"5m": 288, "1h": 24}

# Defaults aligned with config/regimes.yaml. Centralised so the
# downstream `refresh_summaries` script can quote the same numbers
# in `regime_summary.md` without re-parsing yaml.
THRESH = {
    "trend": {
        "ema_minus_slow_min_pct": 0.005,   # 0.5%
        "slope_min": 0.0,
    },
    "vol": {
        "bucket_low_pct": 33.0,
        "bucket_high_pct": 66.0,
        "bucket_history_days": 7,
    },
    "funding": {
        "flat_abs_rate_bp": 1.0,           # |rate| < 1 bp -> flat
        "extreme_abs_rate_bp": 5.0,        # |rate| >= 5 bp -> *_extreme
        "z_extreme_abs": 2.0,              # |z| >= 2 -> *_extreme
    },
    "liquidity": {
        "taker_quote_zscore_thin": -1.0,
        "taker_quote_zscore_thick": 1.0,
    },
}


def _classify_trend(row: pd.Series, t: dict) -> str:
    e = row["ema_fast_minus_slow_pct"]
    s = row["slope_ret_24"]
    if pd.isna(e) or pd.isna(s):
        return "insufficient_data"
    if e > t["ema_minus_slow_min_pct"] and s > t["slope_min"]:
        return "up_trend"
    if e < -t["ema_minus_slow_min_pct"] and s < -t["slope_min"]:
        return "down_trend"
    return "chop"


def _classify_vol(rank: float) -> str:
    if pd.isna(rank):
        return "insufficient_data"
    if rank < THRESH["vol"]["bucket_low_pct"] / 100.0:
        return "low"
    if rank > THRESH["vol"]["bucket_high_pct"] / 100.0:
        return "high"
    return "mid"


def _classify_funding(rate: float, z: float, t: dict) -> str:
    if pd.isna(rate):
        return "insufficient_data"
    flat_abs = t["flat_abs_rate_bp"] / 1e4
    extreme_abs = t["extreme_abs_rate_bp"] / 1e4
    z_ext = t["z_extreme_abs"]
    is_extreme = (abs(rate) >= extreme_abs) or (
        not pd.isna(z) and abs(z) >= z_ext
    )
    if rate > 0:
        if is_extreme:
            return "pos_extreme"
        if abs(rate) < flat_abs:
            return "flat"
        return "pos_normal"
    if rate < 0:
        if is_extreme:
            return "neg_extreme"
        if abs(rate) < flat_abs:
            return "flat"
        return "neg_normal"
    return "flat"


def _classify_basis(b: float) -> str:
    # Basis not ingested in Phase 2/3.
    if pd.isna(b):
        return "insufficient_data"
    if b > 5.0:
        return "premium_rich"
    if b < -5.0:
        return "discount_rich"
    return "neutral"


def _classify_crowding(top_pos: float) -> str:
    # Phase 3 conservative: only `balanced` or `insufficient_data` per
    # the user spec; richer crowded_long / crowded_short is Phase 4.
    if pd.isna(top_pos):
        return "insufficient_data"
    return "balanced"


def _classify_liquidity(z: float, t: dict) -> str:
    if pd.isna(z):
        return "insufficient_data"
    if z < t["taker_quote_zscore_thin"]:
        return "thin"
    if z > t["taker_quote_zscore_thick"]:
        return "thick"
    return "normal"


def build_regimes_for(
    symbol: str,
    timeframe: str,
    store_root: Path,
) -> tuple[Path, int]:
    """Compute per-bar regime labels and write to processed/regimes/."""
    src = store_root / "processed" / "features" / "binance" / symbol / f"{timeframe}.parquet"
    df = pd.read_parquet(src).sort_values("ts_open_ms").reset_index(drop=True)

    # vol bucket via rolling 7-day percentile rank of vol_close_to_close_24
    win = THRESH["vol"]["bucket_history_days"] * BARS_PER_DAY[timeframe]
    min_p = max(win // 2, 24)
    s = df["vol_close_to_close_24"]
    vol_rank = s.rolling(win, min_periods=min_p).apply(
        lambda x: (np.sum(x[:-1] <= x[-1]) / max(len(x) - 1, 1))
        if not np.isnan(x[-1]) else np.nan,
        raw=True,
    )

    out = pd.DataFrame({
        "ts_open_ms": df["ts_open_ms"],
        "ts_close_ms": df["ts_close_ms"],
        "exchange": df["exchange"],
        "symbol": df["symbol"],
        "timeframe": df["timeframe"],
    })

    out["trend_regime"] = df.apply(lambda r: _classify_trend(r, THRESH["trend"]), axis=1)
    out["vol_regime"] = vol_rank.apply(_classify_vol)
    out["funding_regime"] = [
        _classify_funding(r, z, THRESH["funding"])
        for r, z in zip(df["funding_rate_ffill"], df["funding_rate_zscore_30d"])
    ]
    out["basis_regime"] = df["basis_bp"].apply(_classify_basis)
    out["crowding_regime"] = df["top_trader_position_ratio"].apply(_classify_crowding)
    out["liquidity_regime"] = df["taker_quote_zscore_24"].apply(
        lambda z: _classify_liquidity(z, THRESH["liquidity"])
    )

    # composite_label and confidence
    components = ["trend_regime", "vol_regime", "funding_regime",
                  "basis_regime", "crowding_regime", "liquidity_regime"]
    short = {"trend_regime": "T", "vol_regime": "V", "funding_regime": "F",
             "basis_regime": "B", "crowding_regime": "C", "liquidity_regime": "L"}
    composite = []
    confidences = []
    for _, row in out.iterrows():
        parts = []
        good = 0
        for c in components:
            v = row[c]
            tag = "ID" if v == "insufficient_data" else v
            parts.append(f"{short[c]}={tag}")
            if v != "insufficient_data":
                good += 1
        composite.append("|".join(parts))
        confidences.append(round(good / len(components), 3))
    out["composite_label"] = composite
    out["confidence"] = confidences

    out_path = store_root / "processed" / "regimes" / "binance" / symbol / f"{timeframe}.parquet"
    table = pa.Table.from_pandas(out, preserve_index=False)
    write_parquet_atomic(table, out_path)
    return out_path, len(out)


def build_regimes_smoke() -> int:
    """Phase 3 smoke: build regimes for BTCUSDT 5m and 1h."""
    repo_root = Path(__file__).resolve().parents[2]
    store_root = repo_root / "data_layer" / "store"
    for tf in ("5m", "1h"):
        path, n = build_regimes_for("BTCUSDT", tf, store_root)
        print(f"[regimes] BTCUSDT {tf} -> {path.relative_to(repo_root)} rows={n}")
    return 0
