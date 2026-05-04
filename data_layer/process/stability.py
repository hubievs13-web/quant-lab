"""Stability tests for event-conditional outcome cells.

Two complementary tests for each (symbol, timeframe, event_type, horizon)
cell with `n >= MIN_N_CELL` complete outcomes:

1. Walk-forward: split events by `ts_open_ms` into `n_folds` equal-size
   chronological folds, recompute mean forward return and net after fees
   per fold. A cell is "sign-stable" if every fold's net has the same
   sign as the full-sample net.

2. Permutation / bootstrap test: under the null hypothesis that event
   timing is uninformative for forward returns, the observed mean would
   be drawn from the empirical distribution of forward returns at
   uniformly random bars. We sample `n_perms` random index sets of
   the same size as the cell from the underlying bars-joined frame,
   compute their mean forward return at the same horizon, and report
   the two-tailed p-value:

       p = (1 + #{|perm_mean| >= |obs_mean|}) / (n_perms + 1)

The leaderboard already reports `mean_forward_return`, `hit_rate_at_zero`
and `mfe_mae_ratio` per cell; this module is a layer on top that asks
"is the observed edge plausibly random?". It does NOT replace the
Pareto cross-symbol gate; it is an extra evidence requirement before a
hypothesis is allowed into engineer mode.

Outputs (under `data_layer/store/processed/stability/`):

- `binance/<SYMBOL>/<TF>__walk_forward.parquet`
- `binance/<SYMBOL>/<TF>__permutation.parquet`

Schema is documented in `_walk_forward_schema()` and
`_permutation_schema()` below.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from data_layer.ingest.common import write_parquet_atomic

# Minimum number of complete outcomes per cell for either test to run.
# Below this we just emit `n_complete` and `verdict='INSUFFICIENT_N'`.
MIN_N_CELL = 80

# Fee / slippage proxy applied to mean forward return to derive
# `net_after_fee`. Kept identical to refresh_summaries.FEE_PCT so the
# same number is used everywhere. Tier T (taker) round-trip.
FEE_PCT = 0.18

# Maker-tier round-trip friction used by Profile A-Maker. Tracks the
# `_lib/fee_models.BinanceUMMakerFeeModel` accounting (0.02% maker fee
# per side + ~0.03% slippage per side under the proxy adverse-selection
# rule). Reported alongside taker net so we can see which cells the
# maker model rescues.
FEE_PCT_MAKER = 0.10

# Two-tailed permutation p-value threshold below which the cell is
# flagged as "PASS" (edge unlikely to be random under the null).
P_VALUE_PASS = 0.05

# Walk-forward defaults.
N_FOLDS = 3

# Permutation test defaults. 1000 is enough for resolution down to
# ~1% p-values; we use add-one smoothing so p never reaches 0 exactly.
N_PERMS = 1000


def _horizon_bars(horizon: str) -> int:
    """Map a horizon string like 'h+1', 'h+72' to a positive int.

    Returns 1 if the string cannot be parsed; callers should already
    have filtered to legal horizons.
    """
    h = horizon.strip().lower()
    if h.startswith("h+"):
        try:
            return max(1, int(h[2:]))
        except ValueError:
            return 1
    return 1


def _bar_forward_returns(bars: pd.DataFrame, n_bars: int) -> np.ndarray:
    """Compute close-to-close forward returns over `n_bars` for every
    bar in the joined frame.

    Returns a numpy array of length `len(bars)` in the same order as
    bars; the trailing `n_bars` entries are NaN because the future is
    not observable.
    """
    if "close" not in bars.columns or len(bars) == 0:
        return np.array([], dtype=float)
    close = bars["close"].astype(float).to_numpy()
    fr = np.full_like(close, np.nan, dtype=float)
    if len(close) > n_bars:
        fr[:-n_bars] = (close[n_bars:] / close[:-n_bars]) - 1.0
    # Convert to percent so the units match outcomes.forward_return_pct.
    return fr * 100.0


def _walk_forward_one_cell(
    cell_outcomes: pd.DataFrame,
    n_folds: int,
) -> dict[str, float | str | int]:
    """Compute walk-forward stats for one (event_type, horizon) cell.

    `cell_outcomes` must contain columns `ts_open_ms` and
    `forward_return_pct` for the rows belonging to this cell. NaN
    forward returns are dropped before the fold split.
    """
    df = cell_outcomes.dropna(subset=["forward_return_pct"]).copy()
    df = df.sort_values("ts_open_ms").reset_index(drop=True)
    n = len(df)
    full_mean = float(df["forward_return_pct"].mean()) if n else np.nan
    full_net = full_mean - FEE_PCT if not np.isnan(full_mean) else np.nan

    full_net_maker = full_mean - FEE_PCT_MAKER if not np.isnan(full_mean) else np.nan
    out: dict[str, float | str | int] = {
        "n_complete": int(n),
        "full_net": full_net,
        "full_mean": full_mean,
        "full_net_maker": full_net_maker,
    }
    if n < MIN_N_CELL:
        out["verdict"] = "INSUFFICIENT_N"
        for i in range(n_folds):
            out[f"fold{i+1}_n"] = 0
            out[f"fold{i+1}_net"] = np.nan
        out["folds_same_sign"] = 0
        out["sign_stable"] = False
        out["sign_stable_maker"] = False
        out["folds_same_sign_maker"] = 0
        return out

    # Equal-count chronological splits. Last fold absorbs any remainder.
    bounds = [0]
    for i in range(1, n_folds):
        bounds.append((i * n) // n_folds)
    bounds.append(n)
    sign_target = np.sign(full_net) if not np.isnan(full_net) else 0
    sign_target_maker = np.sign(full_net_maker) if not np.isnan(full_net_maker) else 0
    same_sign = 0
    same_sign_maker = 0
    for i in range(n_folds):
        chunk = df.iloc[bounds[i] : bounds[i + 1]]
        m = float(chunk["forward_return_pct"].mean()) if len(chunk) else np.nan
        net = m - FEE_PCT if not np.isnan(m) else np.nan
        net_maker = m - FEE_PCT_MAKER if not np.isnan(m) else np.nan
        out[f"fold{i+1}_n"] = int(len(chunk))
        out[f"fold{i+1}_net"] = net
        out[f"fold{i+1}_net_maker"] = net_maker
        if not np.isnan(net) and sign_target != 0 and np.sign(net) == sign_target:
            same_sign += 1
        if (
            not np.isnan(net_maker)
            and sign_target_maker != 0
            and np.sign(net_maker) == sign_target_maker
        ):
            same_sign_maker += 1
    out["folds_same_sign"] = int(same_sign)
    out["folds_same_sign_maker"] = int(same_sign_maker)
    out["sign_stable"] = bool(same_sign == n_folds)
    out["sign_stable_maker"] = bool(same_sign_maker == n_folds)
    if np.isnan(full_net):
        out["verdict"] = "NO_DATA"
    elif out["sign_stable"]:
        out["verdict"] = "STABLE"
    else:
        out["verdict"] = "UNSTABLE"
    return out


def _permutation_one_cell(
    cell_n: int,
    obs_mean_pct: float,
    bar_returns_pct: np.ndarray,
    rng: np.random.Generator,
    n_perms: int,
) -> dict[str, float | int | str]:
    """Bootstrap p-value: probability that `n` random bars from the
    underlying frame produce a mean forward return at least as
    extreme as the observed mean (two-tailed).

    `bar_returns_pct` must already drop NaN tails; callers should pass
    the array without NaNs so the random draws are valid.
    """
    n_universe = int(len(bar_returns_pct))
    out: dict[str, float | int | str] = {
        "n_perms": int(n_perms),
        "n_universe": n_universe,
        "obs_mean": float(obs_mean_pct) if not np.isnan(obs_mean_pct) else np.nan,
        "obs_net": (
            float(obs_mean_pct) - FEE_PCT if not np.isnan(obs_mean_pct) else np.nan
        ),
        "obs_net_maker": (
            float(obs_mean_pct) - FEE_PCT_MAKER
            if not np.isnan(obs_mean_pct)
            else np.nan
        ),
    }
    if cell_n < MIN_N_CELL or n_universe < cell_n or np.isnan(obs_mean_pct):
        out["p_value"] = np.nan
        out["verdict"] = "INSUFFICIENT_N"
        return out
    # Vectorised random draws. shape=(n_perms, cell_n).
    idx = rng.integers(low=0, high=n_universe, size=(n_perms, cell_n))
    perm_means = bar_returns_pct[idx].mean(axis=1)
    abs_obs = abs(obs_mean_pct)
    extreme = int(np.sum(np.abs(perm_means) >= abs_obs))
    # Add-one smoothing: p in [1/(n+1), 1].
    p_value = (extreme + 1) / (n_perms + 1)
    out["p_value"] = float(p_value)
    out["verdict"] = "PASS" if p_value <= P_VALUE_PASS else "FAIL"
    return out


@dataclass(frozen=True)
class StabilityResult:
    walk_forward: pd.DataFrame
    permutation: pd.DataFrame


def compute_stability_for_series(
    outcomes: pd.DataFrame,
    bars_joined: pd.DataFrame,
    *,
    n_folds: int = N_FOLDS,
    n_perms: int = N_PERMS,
    seed: int = 17,
) -> StabilityResult:
    """Run walk-forward and permutation tests for every cell of a
    single (symbol, timeframe) pair.

    `outcomes` is the per-(event, horizon) outcomes parquet as a
    DataFrame; `bars_joined` is the matching joined-bars parquet.

    Returns two DataFrames; both are keyed by (event_type, horizon).
    """
    if outcomes.empty:
        return StabilityResult(pd.DataFrame(), pd.DataFrame())

    rng = np.random.default_rng(seed)
    horizons = sorted(outcomes["horizon"].unique(), key=_horizon_bars)
    fwd_universe: dict[str, np.ndarray] = {}
    for h in horizons:
        fr = _bar_forward_returns(bars_joined, _horizon_bars(h))
        fwd_universe[h] = fr[~np.isnan(fr)]

    wf_rows: list[dict[str, object]] = []
    perm_rows: list[dict[str, object]] = []
    for (event_type, horizon), grp in outcomes.groupby(
        ["event_type", "horizon"], observed=True
    ):
        wf_stats = _walk_forward_one_cell(grp, n_folds=n_folds)
        wf_stats.update({"event_type": event_type, "horizon": horizon})
        wf_rows.append(wf_stats)

        n_complete = int(wf_stats["n_complete"])
        obs_mean = float(wf_stats["full_mean"])
        perm_stats = _permutation_one_cell(
            cell_n=n_complete,
            obs_mean_pct=obs_mean,
            bar_returns_pct=fwd_universe.get(horizon, np.array([], dtype=float)),
            rng=rng,
            n_perms=n_perms,
        )
        perm_stats.update({"event_type": event_type, "horizon": horizon, "n_complete": n_complete})
        perm_rows.append(perm_stats)

    return StabilityResult(
        walk_forward=pd.DataFrame(wf_rows),
        permutation=pd.DataFrame(perm_rows),
    )


def write_stability_parquets(
    out: StabilityResult,
    *,
    store_root: Path,
    exchange: str,
    symbol: str,
    timeframe: str,
) -> None:
    """Persist a StabilityResult under
    `<store_root>/processed/stability/<exchange>/<SYMBOL>/<TF>__*.parquet`.
    """
    base = store_root / "processed" / "stability" / exchange / symbol
    base.mkdir(parents=True, exist_ok=True)
    if not out.walk_forward.empty:
        wf = out.walk_forward.copy()
        wf["exchange"] = exchange
        wf["symbol"] = symbol
        wf["timeframe"] = timeframe
        write_parquet_atomic(pa.Table.from_pandas(wf), base / f"{timeframe}__walk_forward.parquet")
    if not out.permutation.empty:
        pm = out.permutation.copy()
        pm["exchange"] = exchange
        pm["symbol"] = symbol
        pm["timeframe"] = timeframe
        write_parquet_atomic(pa.Table.from_pandas(pm), base / f"{timeframe}__permutation.parquet")


def run_stability_validation(
    *,
    repo_root: Path,
    store_root: Path,
    symbols: list[str],
    timeframes: list[str],
    n_folds: int = N_FOLDS,
    n_perms: int = N_PERMS,
    seed: int = 17,
) -> dict[tuple[str, str], StabilityResult]:
    """Convenience wrapper that loads the outcomes / bars_joined parquets
    for every (symbol, timeframe), runs both tests, and writes the
    per-cell results to `store_root/processed/stability/...`.
    """
    proc = store_root / "processed"
    results: dict[tuple[str, str], StabilityResult] = {}
    for symbol in symbols:
        for tf in timeframes:
            outcomes_path = proc / "outcomes" / "binance" / symbol / f"{tf}.parquet"
            bars_path = proc / "bars_joined" / "binance" / symbol / f"{tf}.parquet"
            if not outcomes_path.exists() or not bars_path.exists():
                results[(symbol, tf)] = StabilityResult(pd.DataFrame(), pd.DataFrame())
                continue
            outcomes = pd.read_parquet(outcomes_path)
            bars = pd.read_parquet(bars_path)
            result = compute_stability_for_series(
                outcomes,
                bars,
                n_folds=n_folds,
                n_perms=n_perms,
                seed=seed,
            )
            write_stability_parquets(
                result,
                store_root=store_root,
                exchange="binance",
                symbol=symbol,
                timeframe=tf,
            )
            results[(symbol, tf)] = result
    return results
