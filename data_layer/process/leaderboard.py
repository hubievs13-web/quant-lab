"""Event leaderboard for the Market Research Data Layer (Phase 4).

Aggregates `processed/outcomes/...` rows per (event_type, horizon) and
emits `processed/leaderboard/binance/<SYMBOL>/<TF>.parquet`. Long-side
view only in Phase 4 (per-direction split is Phase 5+).

Metrics per (event_type, horizon):

- count: complete (non-NaN forward_return) outcomes only
- count_incomplete: NaN forward_return rows (horizon truncated)
- mean_forward_return: in pct
- median_forward_return
- hit_rate_at_zero: share of complete outcomes with forward_return > 0
- median_mfe, median_mae: in pct
- mfe_mae_ratio: median(mfe) / |median(mae)|, NaN if denominator 0
- sharpe_like: mean / std of forward_return (NaN if n<2 or std=0)
- mean_event_strength: average event_strength across the events
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from data_layer.ingest.common import write_parquet_atomic


def _per_group(g: pd.DataFrame) -> pd.Series:
    fr = g["forward_return_pct"].astype(float)
    fr_complete = fr.dropna()
    n_complete = int(len(fr_complete))
    n_incomplete = int(len(fr) - n_complete)
    if n_complete == 0:
        mean_fr = np.nan
        median_fr = np.nan
        hit_rate = np.nan
        sharpe = np.nan
    else:
        mean_fr = float(fr_complete.mean())
        median_fr = float(fr_complete.median())
        hit_rate = float((fr_complete > 0).mean())
        std = float(fr_complete.std(ddof=1)) if n_complete > 1 else np.nan
        sharpe = (mean_fr / std) if (std and not np.isnan(std) and std != 0) else np.nan

    median_mfe = float(g["mfe_pct"].median()) if g["mfe_pct"].notna().any() else np.nan
    median_mae = float(g["mae_pct"].median()) if g["mae_pct"].notna().any() else np.nan
    if pd.notna(median_mfe) and pd.notna(median_mae) and median_mae != 0:
        mfe_mae_ratio = median_mfe / abs(median_mae)
    else:
        mfe_mae_ratio = np.nan

    return pd.Series({
        "count": n_complete,
        "count_incomplete": n_incomplete,
        "mean_forward_return": mean_fr,
        "median_forward_return": median_fr,
        "hit_rate_at_zero": hit_rate,
        "median_mfe": median_mfe,
        "median_mae": median_mae,
        "mfe_mae_ratio": mfe_mae_ratio,
        "sharpe_like": sharpe,
    })


def build_leaderboard_for(
    symbol: str,
    timeframe: str,
    store_root: Path,
) -> tuple[Path, int]:
    """Aggregate outcomes by (event_type, horizon) and write leaderboard."""
    outcomes_path = (
        store_root / "processed" / "outcomes" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    events_path = (
        store_root / "processed" / "events" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    outcomes = pd.read_parquet(outcomes_path)
    events = pd.read_parquet(events_path)

    if outcomes.empty:
        out = pd.DataFrame(columns=[
            "event_type", "horizon",
            "count", "count_incomplete",
            "mean_forward_return", "median_forward_return",
            "hit_rate_at_zero",
            "median_mfe", "median_mae", "mfe_mae_ratio",
            "sharpe_like", "mean_event_strength",
            "exchange", "symbol", "timeframe",
        ])
    else:
        agg = (
            outcomes
            .groupby(["event_type", "horizon"], dropna=False)
            .apply(_per_group, include_groups=False)
            .reset_index()
        )
        # mean event_strength per event_type
        if not events.empty:
            strength = (
                events.groupby("event_type")["event_strength"].mean().to_dict()
            )
        else:
            strength = {}
        agg["mean_event_strength"] = agg["event_type"].map(strength).astype(float)
        agg["exchange"] = "binance"
        agg["symbol"] = symbol
        agg["timeframe"] = timeframe
        # canonical sort: event_type, horizon (ascending bars)
        agg["_h"] = agg["horizon"].str.replace("h+", "", regex=False).astype(int)
        agg = agg.sort_values(["event_type", "_h"]).drop(columns=["_h"])
        out = agg

    out_path = (
        store_root / "processed" / "leaderboard" / "binance" / symbol
        / f"{timeframe}.parquet"
    )
    table = pa.Table.from_pandas(out, preserve_index=False)
    write_parquet_atomic(table, out_path)
    return out_path, len(out)


def build_leaderboard_smoke() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    store_root = repo_root / "data_layer" / "store"
    for tf in ("5m", "1h"):
        path, n = build_leaderboard_for("BTCUSDT", tf, store_root)
        rel = path.relative_to(repo_root)
        print(f"[leaderboard] BTCUSDT {tf} -> {rel} rows={n}")
    return 0
