"""Unit tests for data_layer.process.stability."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_layer.process.stability import (
    FEE_PCT,
    FEE_PCT_MAKER,
    MIN_N_CELL,
    N_FOLDS,
    P_VALUE_PASS,
    _bar_forward_returns,
    _horizon_bars,
    _permutation_one_cell,
    _walk_forward_one_cell,
    compute_stability_for_series,
)


def test_horizon_bars_parses_h_plus_n():
    assert _horizon_bars("h+1") == 1
    assert _horizon_bars("h+72") == 72
    assert _horizon_bars("h+0") == 1
    assert _horizon_bars("garbage") == 1


def test_bar_forward_returns_aligns_with_close():
    bars = pd.DataFrame({"close": [100.0, 110.0, 121.0, 132.0, np.nan]})
    fr = _bar_forward_returns(bars, n_bars=1)
    assert len(fr) == 5
    # Each step is +10% (100->110, 110->121, 121->132).
    assert abs(fr[0] - 10.0) < 1e-6
    assert abs(fr[1] - 10.0) < 1e-6
    assert abs(fr[2] - 9.090909) < 1e-3
    # last is NaN because the future is unobservable
    assert np.isnan(fr[-1])


def test_bar_forward_returns_returns_pct():
    # 1 -> 1.05 over one bar => +5%.
    bars = pd.DataFrame({"close": [1.0, 1.05]})
    fr = _bar_forward_returns(bars, n_bars=1)
    assert abs(fr[0] - 5.0) < 1e-9


def test_walk_forward_insufficient_n():
    df = pd.DataFrame(
        {
            "ts_open_ms": list(range(10)),
            "forward_return_pct": [0.1] * 10,
        }
    )
    res = _walk_forward_one_cell(df, n_folds=N_FOLDS)
    assert res["verdict"] == "INSUFFICIENT_N"
    assert res["n_complete"] == 10
    assert res["sign_stable"] is False
    assert res["sign_stable_maker"] is False


def test_walk_forward_stable_under_maker_only():
    # Mean of 0.15 is between maker (0.10) and taker (0.18) friction.
    # Net taker = -0.03 (negative); net maker = +0.05 (positive).
    n = MIN_N_CELL + 20
    rng = np.random.default_rng(0)
    fr = rng.normal(loc=0.15, scale=0.01, size=n)  # tight cluster
    df = pd.DataFrame(
        {
            "ts_open_ms": np.arange(n),
            "forward_return_pct": fr,
        }
    )
    res = _walk_forward_one_cell(df, n_folds=N_FOLDS)
    assert res["n_complete"] == n
    assert res["full_mean"] > 0.10
    assert res["full_net"] < 0  # below taker friction
    assert res["full_net_maker"] > 0  # above maker friction
    # Folds should all sit in the same maker-positive region.
    assert res["sign_stable_maker"] is True
    # And taker stability is also "stable" because the noise is tight,
    # so the sign of -0.03 (negative) is consistent across folds.
    assert res["sign_stable"] is True


def test_permutation_p_value_smoke():
    rng = np.random.default_rng(7)
    universe = rng.normal(loc=0.0, scale=1.0, size=10_000)
    obs = 0.0  # truly random observed mean
    res = _permutation_one_cell(
        cell_n=200,
        obs_mean_pct=obs,
        bar_returns_pct=universe,
        rng=rng,
        n_perms=500,
    )
    # p-value with add-one smoothing must be in (0, 1].
    assert 0.0 < res["p_value"] <= 1.0
    # Random observed mean should not pass.
    assert res["verdict"] == "FAIL" or res["p_value"] > P_VALUE_PASS


def test_permutation_extreme_observation_passes():
    rng = np.random.default_rng(7)
    universe = rng.normal(loc=0.0, scale=0.05, size=20_000)
    # An observed mean 20 stds away is overwhelmingly improbable.
    res = _permutation_one_cell(
        cell_n=200,
        obs_mean_pct=10.0,
        bar_returns_pct=universe,
        rng=rng,
        n_perms=500,
    )
    assert res["verdict"] == "PASS"
    assert res["p_value"] < 0.01


def test_permutation_insufficient_n_returns_nan():
    rng = np.random.default_rng(0)
    universe = rng.normal(size=1_000)
    res = _permutation_one_cell(
        cell_n=10,  # below MIN_N_CELL
        obs_mean_pct=0.5,
        bar_returns_pct=universe,
        rng=rng,
        n_perms=100,
    )
    assert res["verdict"] == "INSUFFICIENT_N"
    assert np.isnan(res["p_value"])


def test_compute_stability_for_series_smoke():
    # Build a tiny synthetic outcomes/bars pair with one known event
    # cell that crosses the n>=80 threshold and should be evaluable.
    n_bars = 1000
    rng = np.random.default_rng(3)
    bars = pd.DataFrame(
        {
            "ts_open_ms": np.arange(n_bars) * 60_000,
            "close": np.cumprod(1 + rng.normal(scale=0.001, size=n_bars)),
        }
    )
    # Synthesise outcomes for 100 events at random bar indices, with
    # forward_return_pct sampled around 0 for h+1.
    n_events = 100
    event_idx = rng.integers(low=0, high=n_bars - 5, size=n_events)
    events = pd.DataFrame(
        {
            "ts_open_ms": bars["ts_open_ms"].iloc[event_idx].to_numpy(),
            "event_type": ["EV_TEST"] * n_events,
            "horizon": ["h+1"] * n_events,
            "forward_return_pct": rng.normal(loc=0.0, scale=0.1, size=n_events),
        }
    )
    res = compute_stability_for_series(events, bars, n_perms=100)
    assert not res.walk_forward.empty
    assert not res.permutation.empty
    assert "EV_TEST" in res.walk_forward["event_type"].tolist()
    # On random data the cell should rarely pass at p<=0.05, but the
    # function must always emit a verdict.
    assert res.permutation["verdict"].iloc[0] in {"PASS", "FAIL", "INSUFFICIENT_N"}


def test_fee_constants_consistency():
    # Maker friction must be strictly less than taker friction; this
    # is the entire point of Profile A-Maker.
    assert FEE_PCT_MAKER < FEE_PCT
    # And the canonical taker number must match the rest of the
    # data layer (refresh_summaries.FEE_PCT).
    from data_layer.scripts.refresh_summaries import FEE_PCT as RS_FEE_PCT

    assert FEE_PCT == RS_FEE_PCT
