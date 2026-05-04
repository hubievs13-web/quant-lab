"""Unit tests for refresh_research_candidates_summary."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_layer.scripts import refresh_summaries as rs


def _seed_stability(
    tmp_root: Path,
    *,
    btc_5m_wf: pd.DataFrame,
    btc_5m_pm: pd.DataFrame,
    eth_5m_wf: pd.DataFrame | None = None,
    eth_5m_pm: pd.DataFrame | None = None,
) -> None:
    base = tmp_root / "processed" / "stability" / "binance"
    (base / "BTCUSDT").mkdir(parents=True, exist_ok=True)
    btc_5m_wf.to_parquet(base / "BTCUSDT" / "5m__walk_forward.parquet")
    btc_5m_pm.to_parquet(base / "BTCUSDT" / "5m__permutation.parquet")
    if eth_5m_wf is not None:
        (base / "ETHUSDT").mkdir(parents=True, exist_ok=True)
        eth_5m_wf.to_parquet(base / "ETHUSDT" / "5m__walk_forward.parquet")
        eth_5m_pm.to_parquet(base / "ETHUSDT" / "5m__permutation.parquet")


def _wf_row(symbol: str, n: int, mean: float, stable_t: bool, stable_m: bool):
    return {
        "symbol": symbol,
        "timeframe": "5m",
        "event_type": "EV_DEMO",
        "horizon": "h+12",
        "n_complete": n,
        "full_mean": mean,
        "full_net": mean - 0.18,
        "full_net_maker": mean - 0.10,
        "fold1_n": n // 3,
        "fold2_n": n // 3,
        "fold3_n": n - 2 * (n // 3),
        "fold1_net": mean - 0.18,
        "fold2_net": mean - 0.18,
        "fold3_net": mean - 0.18,
        "fold1_net_maker": mean - 0.10,
        "fold2_net_maker": mean - 0.10,
        "fold3_net_maker": mean - 0.10,
        "folds_same_sign": 3 if stable_t else 1,
        "folds_same_sign_maker": 3 if stable_m else 1,
        "sign_stable": stable_t,
        "sign_stable_maker": stable_m,
        "verdict": "STABLE",
    }


def _pm_row(symbol: str, n: int, mean: float, p: float):
    return {
        "symbol": symbol,
        "timeframe": "5m",
        "event_type": "EV_DEMO",
        "horizon": "h+12",
        "n_complete": n,
        "obs_mean": mean,
        "obs_net": mean - 0.18,
        "obs_net_maker": mean - 0.10,
        "p_value": p,
        "n_perms": 1000,
        "n_universe": 50_000,
        "verdict": "PASS" if p <= 0.05 else "FAIL",
    }


def _patch_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rs, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rs, "STORE_ROOT", tmp_path)
    monkeypatch.setattr(rs, "REPORTS", tmp_path / "reports")


def test_research_candidates_writes_empty_when_no_pass(tmp_path, monkeypatch):
    # Cell that fails permutation (p>0.05) should produce empty Tier T
    # and Tier M sections.
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 100, 0.20, True, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 100, 0.20, p=0.30)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(tmp_path, btc_5m_wf=btc_wf, btc_5m_pm=btc_pm)
    rc = rs.refresh_research_candidates_summary()
    assert rc == 0
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    assert "## Tier T single-symbol candidates" in out
    assert "## Tier M single-symbol candidates" in out
    # The cell does not pass either tier (p=0.30 > 0.10), so both
    # single-symbol sections must say None.
    tier_t_block = out.split("## Tier T single-symbol")[1].split("## Tier M")[0]
    tier_m_block = out.split("## Tier M single-symbol")[1]
    assert "None" in tier_t_block
    assert "None" in tier_m_block


def test_research_candidates_lists_tier_m_pass(tmp_path, monkeypatch):
    # Cell with maker net > 0, M sign-stable, p=0.08 (passes Tier M
    # 0.10 threshold but fails Tier T 0.05).
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 120, 0.15, False, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 120, 0.15, p=0.08)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(tmp_path, btc_5m_wf=btc_wf, btc_5m_pm=btc_pm)
    rs.refresh_research_candidates_summary()
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    tier_m_block = out.split("## Tier M single-symbol")[1]
    assert "BTCUSDT" in tier_m_block
    assert "DEMO" in tier_m_block
    # Tier T section must remain empty because permutation fails 0.05.
    tier_t_block = out.split("## Tier T single-symbol")[1].split("## Tier M")[0]
    assert "None" in tier_t_block


def test_research_candidates_cross_symbol_section(tmp_path, monkeypatch):
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 110, 0.40, True, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 110, 0.40, p=0.01)])
    eth_wf = pd.DataFrame([_wf_row("ETHUSDT", 90, 0.35, True, True)])
    eth_pm = pd.DataFrame([_pm_row("ETHUSDT", 90, 0.35, p=0.02)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(
        tmp_path,
        btc_5m_wf=btc_wf,
        btc_5m_pm=btc_pm,
        eth_5m_wf=eth_wf,
        eth_5m_pm=eth_pm,
    )
    rs.refresh_research_candidates_summary()
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    cross_block = out.split("## Cross-symbol Pareto")[1].split("## Tier T")[0]
    assert "BTC n" in cross_block  # header rendered
    assert "DEMO" in cross_block  # event surfaced
    assert "| T | 5m | DEMO | h+12 |" in cross_block
