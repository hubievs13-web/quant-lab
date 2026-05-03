"""Event detection engine for the Market Research Data Layer (Phase 4).

Reads `processed/features/binance/<SYMBOL>/<TF>.parquet` plus
`processed/regimes/...` for `context_regime` and writes
`processed/events/binance/<SYMBOL>/<TF>.parquet`.

Each event is a discrete `(ts_open_ms, event_type)` row. We register
the **first cross** only (condition true at bar i, false at bar i-1)
to avoid consecutive-bar cascades. Anti-lookahead is enforced because
all inputs are features at bar i (functions of bars <= i).

Implemented event types:
- EV_FUND_FLIP, EV_FUND_EXTREME, EV_OI_SPIKE_UP, EV_OI_FLUSH,
  EV_VOL_BREAKOUT, EV_FUNDING_WINDOW_PRE,
- EV_PREMIUM_SPIKE, EV_PREMIUM_COMPRESSION (basis_zscore_24).

Skipped (insufficient source data; documented in the catalog):
- EV_LIQ_LONG_CASCADE, EV_LIQ_SHORT_CASCADE (no liquidations ingest).
- EV_CROWD_FLIP (LSR z-score requires >= 30 days of OI metrics).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from data_layer.ingest.common import write_parquet_atomic

BARS_PER_DAY = {"5m": 288, "1h": 24}

# Source-of-truth thresholds; mirrored in `config/events.yaml`.
THRESH = {
    "EV_FUND_FLIP": {
        "min_abs_rate_change_bp": 0.5,
    },
    "EV_FUND_EXTREME": {
        "zscore_abs_threshold": 2.0,
        "fallback_abs_rate_bp": 5.0,
    },
    "EV_OI_SPIKE_UP": {
        "oi_pct_change_1h_min": 0.03,
        "oi_zscore_30d_min": 1.0,
    },
    "EV_OI_FLUSH": {
        "oi_pct_change_1h_max": -0.03,
    },
    "EV_VOL_BREAKOUT": {
        "range_pct_pctile": 99.0,
        "taker_quote_zscore_24_min": 2.0,
        "rolling_history_days_target": 30,
        "rolling_min_periods_days": 3,
    },
    "EV_FUNDING_WINDOW_PRE": {
        "pre_settle_minutes": 30,
    },
    "EV_PREMIUM_SPIKE": {
        "basis_zscore_24_min": 2.0,
    },
    "EV_PREMIUM_COMPRESSION": {
        "basis_zscore_24_max": -2.0,
    },
}

IMPLEMENTED_EVENT_TYPES: tuple[str, ...] = tuple(THRESH.keys())

SKIPPED_EVENT_TYPES: dict[str, str] = {
    "EV_LIQ_LONG_CASCADE": "no liquidations ingest in v1",
    "EV_LIQ_SHORT_CASCADE": "no liquidations ingest in v1",
    "EV_CROWD_FLIP": "LSR z-score requires >= 30 days of OI metrics history",
}


def _event_id(symbol: str, tf: str, ev: str, ts: int) -> str:
    h = hashlib.sha1(f"{symbol}|{tf}|{ev}|{ts}".encode("utf-8")).hexdigest()
    return h[:16]


def _first_cross(condition: pd.Series) -> pd.Series:
    """Return True only on bars where condition transitions False -> True."""
    cond = condition.fillna(False).astype(bool)
    prev = cond.shift(1, fill_value=False)
    return cond & ~prev


def _detect_fund_flip(df: pd.DataFrame) -> pd.DataFrame:
    """Sign change between consecutive *funding settles* (not between bars)."""
    rate = df["funding_rate_ffill"]
    # Only fire on the bar where funding_minutes_to_next == funding_interval -1
    # i.e. the bar where the new settle has just been observed: rate value
    # changed vs prior bar AND the change crossed zero.
    prev_rate = rate.shift(1)
    flipped = (
        rate.notna()
        & prev_rate.notna()
        & (np.sign(rate) != np.sign(prev_rate))
        & (np.sign(rate) != 0)
        & (np.sign(prev_rate) != 0)
        & ((rate - prev_rate).abs() * 1e4
           >= THRESH["EV_FUND_FLIP"]["min_abs_rate_change_bp"])
    )
    idx = df.index[flipped]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = ((rate.loc[idx] - prev_rate.loc[idx]).abs() * 1e4).astype(float)
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_FUND_FLIP",
        "event_strength": strength.values,
    })


def _detect_fund_extreme(df: pd.DataFrame) -> pd.DataFrame:
    z = df["funding_rate_zscore_30d"]
    rate = df["funding_rate_ffill"]
    z_thr = THRESH["EV_FUND_EXTREME"]["zscore_abs_threshold"]
    fb_thr = THRESH["EV_FUND_EXTREME"]["fallback_abs_rate_bp"] / 1e4
    cond_z = z.abs() >= z_thr
    cond_fb = z.isna() & (rate.abs() >= fb_thr)
    cond = cond_z | cond_fb
    fires = _first_cross(cond)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = []
    for i in idx:
        zv = z.loc[i]
        if pd.notna(zv):
            strength.append(float(abs(zv)))
        else:
            strength.append(float(abs(rate.loc[i]) * 1e4 / fb_thr / 1e4 * z_thr))
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_FUND_EXTREME",
        "event_strength": strength,
    })


def _detect_oi_spike_up(df: pd.DataFrame) -> pd.DataFrame:
    pct = df["oi_pct_change_1h"]
    z = df["oi_zscore_30d"]
    pct_min = THRESH["EV_OI_SPIKE_UP"]["oi_pct_change_1h_min"]
    z_min = THRESH["EV_OI_SPIKE_UP"]["oi_zscore_30d_min"]
    cond = (pct > pct_min) & (z.isna() | (z > z_min))
    fires = _first_cross(cond)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = []
    for i in idx:
        zv = z.loc[i]
        pv = pct.loc[i]
        # event_strength in z-units: prefer real z, else pct/pct_min.
        if pd.notna(zv):
            strength.append(float(zv))
        else:
            strength.append(float(pv / pct_min))
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_OI_SPIKE_UP",
        "event_strength": strength,
    })


def _detect_oi_flush(df: pd.DataFrame) -> pd.DataFrame:
    pct = df["oi_pct_change_1h"]
    pct_max = THRESH["EV_OI_FLUSH"]["oi_pct_change_1h_max"]  # negative
    cond = pct < pct_max
    fires = _first_cross(cond)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = (pct.loc[idx].abs() / abs(pct_max)).astype(float).values
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_OI_FLUSH",
        "event_strength": strength,
    })


def _detect_vol_breakout(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    rng = df["range_pct"]
    z = df["taker_quote_zscore_24"]
    cfg = THRESH["EV_VOL_BREAKOUT"]
    bpd = BARS_PER_DAY[tf]
    target_bars = cfg["rolling_history_days_target"] * bpd
    win = min(target_bars, len(df))
    min_p = max(cfg["rolling_min_periods_days"] * bpd, 24)
    pct = cfg["range_pct_pctile"] / 100.0
    rolling_q = rng.rolling(win, min_periods=min_p).quantile(pct)
    cond = (rng >= rolling_q) & (z > cfg["taker_quote_zscore_24_min"])
    fires = _first_cross(cond)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = z.loc[idx].astype(float).values
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_VOL_BREAKOUT",
        "event_strength": strength,
    })


def _detect_premium_spike(df: pd.DataFrame) -> pd.DataFrame:
    if "basis_zscore_24" not in df.columns:
        return pd.DataFrame()
    z = df["basis_zscore_24"]
    z_min = THRESH["EV_PREMIUM_SPIKE"]["basis_zscore_24_min"]
    cond = z >= z_min
    fires = _first_cross(cond)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = z.loc[idx].astype(float).values
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_PREMIUM_SPIKE",
        "event_strength": strength,
    })


def _detect_premium_compression(df: pd.DataFrame) -> pd.DataFrame:
    if "basis_zscore_24" not in df.columns:
        return pd.DataFrame()
    z = df["basis_zscore_24"]
    z_max = THRESH["EV_PREMIUM_COMPRESSION"]["basis_zscore_24_max"]  # negative
    cond = z <= z_max
    fires = _first_cross(cond)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    strength = z.loc[idx].abs().astype(float).values
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_PREMIUM_COMPRESSION",
        "event_strength": strength,
    })


def _detect_funding_window_pre(df: pd.DataFrame) -> pd.DataFrame:
    flag = df["pre_funding_30m"].fillna(0).astype(int) == 1
    fires = _first_cross(flag)
    idx = df.index[fires]
    if len(idx) == 0:
        return pd.DataFrame()
    mtn = df["funding_minutes_to_next"].loc[idx]
    strength = ((30 - mtn.clip(lower=0, upper=30)) / 30).astype(float).values
    return pd.DataFrame({
        "row_idx": idx,
        "ts_open_ms": df.loc[idx, "ts_open_ms"].values,
        "event_type": "EV_FUNDING_WINDOW_PRE",
        "event_strength": strength,
    })


def detect_events_for(
    symbol: str,
    timeframe: str,
    store_root: Path,
) -> tuple[Path, int, dict[str, int]]:
    """Detect events and write `processed/events/.../<TF>.parquet`."""
    feat_path = (
        store_root / "processed" / "features" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    reg_path = (
        store_root / "processed" / "regimes" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    feats = (
        pd.read_parquet(feat_path)
        .sort_values("ts_open_ms")
        .reset_index(drop=True)
    )
    regs = (
        pd.read_parquet(reg_path)
        .sort_values("ts_open_ms")
        .reset_index(drop=True)
    )

    detectors = {
        "EV_FUND_FLIP": _detect_fund_flip(feats),
        "EV_FUND_EXTREME": _detect_fund_extreme(feats),
        "EV_OI_SPIKE_UP": _detect_oi_spike_up(feats),
        "EV_OI_FLUSH": _detect_oi_flush(feats),
        "EV_VOL_BREAKOUT": _detect_vol_breakout(feats, timeframe),
        "EV_FUNDING_WINDOW_PRE": _detect_funding_window_pre(feats),
        "EV_PREMIUM_SPIKE": _detect_premium_spike(feats),
        "EV_PREMIUM_COMPRESSION": _detect_premium_compression(feats),
    }
    parts = [d for d in detectors.values() if not d.empty]
    counts = {k: int(len(v)) for k, v in detectors.items()}
    if not parts:
        out = pd.DataFrame(columns=[
            "event_id", "ts_open_ms", "event_type", "event_strength",
            "context_regime", "exchange", "symbol", "timeframe",
        ])
    else:
        ev = pd.concat(parts, ignore_index=True).sort_values(
            ["ts_open_ms", "event_type"]
        ).reset_index(drop=True)
        # context_regime is the composite_label at the same bar
        regime_by_ts = regs.set_index("ts_open_ms")["composite_label"]
        ev["context_regime"] = ev["ts_open_ms"].map(regime_by_ts).fillna("unknown")
        ev["exchange"] = "binance"
        ev["symbol"] = symbol
        ev["timeframe"] = timeframe
        ev["event_id"] = [
            _event_id(symbol, timeframe, t, int(ts))
            for t, ts in zip(ev["event_type"], ev["ts_open_ms"])
        ]
        out = ev[[
            "event_id", "ts_open_ms", "event_type", "event_strength",
            "context_regime", "exchange", "symbol", "timeframe",
        ]]

    out_path = (
        store_root / "processed" / "events" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    table = pa.Table.from_pandas(out, preserve_index=False)
    write_parquet_atomic(table, out_path)
    return out_path, len(out), counts


def detect_events_smoke() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    store_root = repo_root / "data_layer" / "store"
    for tf in ("5m", "1h"):
        path, n, counts = detect_events_for("BTCUSDT", tf, store_root)
        rel = path.relative_to(repo_root)
        breakdown = ", ".join(
            f"{k}={v}" for k, v in counts.items() if v > 0
        ) or "no events"
        print(f"[events] BTCUSDT {tf} -> {rel} rows={n} [{breakdown}]")
    return 0
