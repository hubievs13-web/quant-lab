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
    assert "## Tier T long candidates" in out
    assert "## Tier M long candidates" in out
    assert "## Tier T fade candidates" in out
    assert "## Tier M fade candidates" in out
    # The cell does not pass either tier (p=0.30 > 0.10), so all four
    # sections must say None.
    for header in (
        "## Tier T long candidates",
        "## Tier M long candidates",
        "## Tier T fade candidates",
        "## Tier M fade candidates",
    ):
        block = out.split(header)[1].split("## ", 1)[0] if "## " in out.split(header)[1] else out.split(header)[1]
        assert "None" in block


def test_research_candidates_lists_tier_m_pass(tmp_path, monkeypatch):
    # Cell with maker net > 0, M sign-stable, p=0.08 (passes Tier M
    # 0.10 threshold but fails Tier T 0.05).
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 120, 0.15, False, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 120, 0.15, p=0.08)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(tmp_path, btc_5m_wf=btc_wf, btc_5m_pm=btc_pm)
    rs.refresh_research_candidates_summary()
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    # The cell appears in the Tier M long section and nowhere else.
    tier_m_long = out.split("## Tier M long candidates")[1].split("## ")[0]
    tier_t_long = out.split("## Tier T long candidates")[1].split("## ")[0]
    tier_m_fade = out.split("## Tier M fade candidates")[1].split("## ")[0]
    assert "BTCUSDT" in tier_m_long
    assert "DEMO" in tier_m_long
    assert "None" in tier_t_long
    assert "None" in tier_m_fade


def test_research_candidates_lists_fade_when_negative_net(tmp_path, monkeypatch):
    # Cell with full_mean = -0.40 (so full_net = -0.58, full_net_maker
    # = -0.50), sign-stable in both directions, p=0.01 (passes both
    # Tier T 0.05 and Tier M 0.10 thresholds). Must surface in
    # Tier T fade and Tier M fade sections (not in any long section).
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 150, -0.40, True, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 150, -0.40, p=0.01)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(tmp_path, btc_5m_wf=btc_wf, btc_5m_pm=btc_pm)
    rs.refresh_research_candidates_summary()
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    tier_t_long = out.split("## Tier T long candidates")[1].split("## ")[0]
    tier_m_long = out.split("## Tier M long candidates")[1].split("## ")[0]
    tier_t_fade = out.split("## Tier T fade candidates")[1].split("## ")[0]
    tier_m_fade = out.split("## Tier M fade candidates")[1].split("## ")[0]
    assert "None" in tier_t_long
    assert "None" in tier_m_long
    assert "BTCUSDT" in tier_t_fade
    assert "BTCUSDT" in tier_m_fade
    assert "DEMO" in tier_t_fade
    assert "DEMO" in tier_m_fade


def test_research_candidates_excludes_fade_when_mean_within_friction(tmp_path, monkeypatch):
    # Bug fix regression: a cell with `full_mean` slightly positive
    # (e.g. +0.01%) and Tier T friction 0.18% has `full_net = -0.17%`.
    # The pre-fix filter `full_net < 0` would (incorrectly) surface
    # this in the fade section, but a fade trade pays friction *again*
    # on a near-zero shorted return -> realised fade net = -0.19% (loss).
    # The corrected filter requires `full_mean < -friction`, so this
    # cell must NOT appear in any fade section.
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 200, 0.01, True, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 200, 0.01, p=0.01)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(tmp_path, btc_5m_wf=btc_wf, btc_5m_pm=btc_pm)
    rs.refresh_research_candidates_summary()
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    tier_t_fade = out.split("## Tier T fade candidates")[1].split("## ")[0]
    tier_m_fade = out.split("## Tier M fade candidates")[1].split("## ")[0]
    assert "None" in tier_t_fade
    assert "None" in tier_m_fade


def test_research_candidates_fade_displays_positive_fade_direction_net(tmp_path, monkeypatch):
    # full_mean = -0.40% means a fade trade earns +0.40% raw and
    # +0.22% net (Tier T) / +0.30% net (Tier M) after the matching
    # tier's friction. The displayed `net` column in fade sections
    # must reflect this realised fade-direction net, not the long-
    # direction net.
    btc_wf = pd.DataFrame([_wf_row("BTCUSDT", 150, -0.40, True, True)])
    btc_pm = pd.DataFrame([_pm_row("BTCUSDT", 150, -0.40, p=0.01)])
    _patch_paths(monkeypatch, tmp_path)
    _seed_stability(tmp_path, btc_5m_wf=btc_wf, btc_5m_pm=btc_pm)
    rs.refresh_research_candidates_summary()
    out = (tmp_path / "reports" / "summaries" / "research_candidates.md").read_text()
    tier_t_fade = out.split("## Tier T fade candidates")[1].split("## ")[0]
    tier_m_fade = out.split("## Tier M fade candidates")[1].split("## ")[0]
    # Tier T fade net = -(-0.40) - 0.18 = +0.22% ; Tier M = +0.30%
    assert "+0.22%" in tier_t_fade
    assert "+0.30%" in tier_m_fade
    # And no negative-net rendering in either fade section anymore.
    assert "-0.58%" not in tier_t_fade
    assert "-0.50%" not in tier_m_fade


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
    assert "| T | long | 5m | DEMO | h+12 |" in cross_block
