"""Forward-outcome engine for the Market Research Data Layer (Phase 4).

For each event row, anchor on the bar that closes strictly **after**
the event bar (next-bar entry). For each horizon h, compute:

- forward_return_pct = (close[t+h] - close[t]) / close[t] * 100
- mfe_pct = max over (t, t+h] of (high - close[t]) / close[t] * 100
- mae_pct = min over (t, t+h] of (low  - close[t]) / close[t] * 100
- time_to_mfe_bars / time_to_mae_bars = arg{max,min} - t
- max_holding_bars_used = h (or fewer if window truncated)

If `t + h > last_bar_index`, the outcome is marked **incomplete** by
returning NaN for forward_return / mfe / mae and `max_holding_bars_used`
clipped to whatever bars were actually available. No future-bar
guesses are inferred.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from data_layer.ingest.common import write_parquet_atomic

# Horizons mirrored from `config/events.yaml` and the plan Section 7.
HORIZONS = {
    "5m": [1, 3, 12, 72],
    "1h": [1, 3, 12, 24, 72],
}


def _compute_outcomes_for_event(
    bars: pd.DataFrame,
    event_idx: int,
    horizons: list[int],
) -> list[dict]:
    """Compute outcomes for a single event at bars index `event_idx`.

    Returns one dict per horizon. Anchor t = event_idx + 1 (bar after
    the event bar). Window k in [t+1, t+h] is sampled for MFE/MAE.
    """
    rows: list[dict] = []
    n = len(bars)
    t = event_idx + 1
    if t >= n:
        # No anchor bar exists; emit NaN rows for all horizons.
        for h in horizons:
            rows.append({
                "horizon": f"h+{h}",
                "forward_return_pct": np.nan,
                "mfe_pct": np.nan,
                "mae_pct": np.nan,
                "time_to_mfe_bars": np.nan,
                "time_to_mae_bars": np.nan,
                "max_holding_bars_used": 0,
            })
        return rows

    close_t = float(bars.iloc[t]["close"])
    if not np.isfinite(close_t) or close_t == 0.0:
        for h in horizons:
            rows.append({
                "horizon": f"h+{h}",
                "forward_return_pct": np.nan,
                "mfe_pct": np.nan,
                "mae_pct": np.nan,
                "time_to_mfe_bars": np.nan,
                "time_to_mae_bars": np.nan,
                "max_holding_bars_used": 0,
            })
        return rows

    high = bars["high"].values
    low = bars["low"].values
    close = bars["close"].values

    for h in horizons:
        end = t + h
        complete = end < n
        used = h if complete else max(0, n - 1 - t)
        win_start = t + 1
        win_end = end if complete else n - 1
        if win_end < win_start or used == 0:
            rows.append({
                "horizon": f"h+{h}",
                "forward_return_pct": np.nan,
                "mfe_pct": np.nan,
                "mae_pct": np.nan,
                "time_to_mfe_bars": np.nan,
                "time_to_mae_bars": np.nan,
                "max_holding_bars_used": used,
            })
            continue

        if complete:
            fr = (close[end] - close_t) / close_t * 100.0
        else:
            fr = np.nan

        slc_high = high[win_start: win_end + 1]
        slc_low = low[win_start: win_end + 1]
        mfe_idx = int(np.nanargmax(slc_high))
        mae_idx = int(np.nanargmin(slc_low))
        mfe = (slc_high[mfe_idx] - close_t) / close_t * 100.0
        mae = (slc_low[mae_idx] - close_t) / close_t * 100.0
        rows.append({
            "horizon": f"h+{h}",
            "forward_return_pct": float(fr) if pd.notna(fr) else np.nan,
            "mfe_pct": float(mfe),
            "mae_pct": float(mae),
            "time_to_mfe_bars": int(mfe_idx + 1),
            "time_to_mae_bars": int(mae_idx + 1),
            "max_holding_bars_used": int(used),
        })
    return rows


def build_outcomes_for(
    symbol: str,
    timeframe: str,
    store_root: Path,
) -> tuple[Path, int]:
    """Build forward-outcome rows for every event in the events parquet."""
    bars_path = (
        store_root / "processed" / "bars_joined" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    events_path = (
        store_root / "processed" / "events" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    bars = (
        pd.read_parquet(bars_path)
        .sort_values("ts_open_ms")
        .reset_index(drop=True)
    )
    events = (
        pd.read_parquet(events_path)
        .sort_values("ts_open_ms")
        .reset_index(drop=True)
    )
    horizons = HORIZONS[timeframe]

    if events.empty:
        out = pd.DataFrame(columns=[
            "event_id", "ts_open_ms", "event_type", "horizon",
            "forward_return_pct", "mfe_pct", "mae_pct",
            "time_to_mfe_bars", "time_to_mae_bars",
            "max_holding_bars_used",
            "exchange", "symbol", "timeframe",
        ])
    else:
        ts_to_idx = {int(t): i for i, t in enumerate(bars["ts_open_ms"].values)}
        out_rows: list[dict] = []
        for _, ev in events.iterrows():
            idx = ts_to_idx.get(int(ev["ts_open_ms"]))
            if idx is None:
                continue
            for r in _compute_outcomes_for_event(bars, idx, horizons):
                r.update({
                    "event_id": ev["event_id"],
                    "ts_open_ms": int(ev["ts_open_ms"]),
                    "event_type": ev["event_type"],
                    "exchange": "binance",
                    "symbol": symbol,
                    "timeframe": timeframe,
                })
                out_rows.append(r)
        out = pd.DataFrame(out_rows)
        out = out[[
            "event_id", "ts_open_ms", "event_type", "horizon",
            "forward_return_pct", "mfe_pct", "mae_pct",
            "time_to_mfe_bars", "time_to_mae_bars",
            "max_holding_bars_used",
            "exchange", "symbol", "timeframe",
        ]]

    out_path = (
        store_root / "processed" / "outcomes" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    table = pa.Table.from_pandas(out, preserve_index=False)
    write_parquet_atomic(table, out_path)
    return out_path, len(out)


def build_outcomes_smoke() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    store_root = repo_root / "data_layer" / "store"
    for tf in ("5m", "1h"):
        path, n = build_outcomes_for("BTCUSDT", tf, store_root)
        rel = path.relative_to(repo_root)
        print(f"[outcomes] BTCUSDT {tf} -> {rel} rows={n}")
    return 0
