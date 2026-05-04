"""Regenerate compact Codex-readable markdown summaries."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from data_layer.process.events import IMPLEMENTED_EVENT_TYPES, SKIPPED_EVENT_TYPES
from data_layer.process.features import FEATURE_SPECS

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
REPORTS = REPO_ROOT / "data_layer" / "reports"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
TIMEFRAMES = ("5m", "1h")
REPORT_CAP_BYTES = 5 * 1024
FEE_PCT = 0.18
MIN_COUNT_FOR_RANKING = 30
PARETO_MIN_N = 80

IMPLEMENTED_DESC = {
    "EV_FUND_FLIP": "funding_rate sign change between consecutive bars (>= 0.5 bp move)",
    "EV_FUND_EXTREME": "|funding_rate_zscore_30d| >= 2 (or |rate| >= 5 bp fallback)",
    "EV_OI_SPIKE_UP": "oi_pct_change_1h > +3% AND (oi_zscore_30d > 1 OR z insufficient)",
    "EV_OI_FLUSH": "oi_pct_change_1h < -3%",
    "EV_VOL_BREAKOUT": "range_pct >= rolling 99-pctile AND taker_quote_zscore_24 > 2",
    "EV_FUNDING_WINDOW_PRE": "informational; minutes_to_next_settle <= 30 (first cross)",
    "EV_PREMIUM_SPIKE": "basis_zscore_24 >= +2 (mark - index spread spikes positive)",
    "EV_PREMIUM_COMPRESSION": "basis_zscore_24 <= -2 (mark - index spread spikes negative)",
}


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")


def _proc_path(kind: str, symbol: str, tf: str) -> Path:
    return STORE_ROOT / "processed" / kind / "binance" / symbol / f"{tf}.parquet"


def _read_meta(p: Path) -> tuple[int, int | None, int | None]:
    if not p.exists():
        return 0, None, None
    schema = pq.read_schema(p)
    if "ts_open_ms" not in schema.names:
        n = pq.ParquetFile(p).metadata.num_rows
        return n, None, None
    t = pq.read_table(p, columns=["ts_open_ms"])
    n = t.num_rows
    if n == 0:
        return 0, None, None
    arr = t.column("ts_open_ms")
    return n, arr[0].as_py(), arr[-1].as_py()


def _ms_to_str(ms: int | None) -> str:
    if ms is None:
        return "-"
    t = dt.datetime.fromtimestamp(ms / 1000, tz=dt.UTC)
    return t.strftime("%Y-%m-%d %H:%M UTC")


def _write_capped(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines) + "\n"
    if len(text.encode("utf-8")) > REPORT_CAP_BYTES:
        raise RuntimeError(f"Report {path} exceeds 5 KB cap.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _fmt_pct(v: float) -> str:
    if pd.isna(v):
        return "-"
    return f"{v:+.2f}%"


def _fmt_ratio(v: float) -> str:
    if pd.isna(v):
        return "-"
    return f"{v:.2f}"


def _read_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _load_leaderboards() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            df = _read_df(_proc_path("leaderboard", symbol, tf))
            if df.empty:
                continue
            df = df.copy()
            df["symbol"] = symbol
            df["timeframe"] = tf
            df["net_after_fee"] = df["mean_forward_return"] - FEE_PCT
            rows.append(df)
    if not rows:
        return pd.DataFrame()
    merged = pd.concat(rows, ignore_index=True)
    merged["_h"] = merged["horizon"].str.replace("h+", "", regex=False).astype(int)
    return merged


def _pair_rows(lb: pd.DataFrame) -> pd.DataFrame:
    if lb.empty:
        return pd.DataFrame()
    keys = ["event_type", "timeframe", "horizon"]
    btc = lb[lb["symbol"] == "BTCUSDT"][keys + [
        "count", "mean_forward_return", "hit_rate_at_zero", "mfe_mae_ratio", "net_after_fee"
    ]].rename(columns={
        "count": "btc_count",
        "mean_forward_return": "btc_mean",
        "hit_rate_at_zero": "btc_hit",
        "mfe_mae_ratio": "btc_ratio",
        "net_after_fee": "btc_net",
    })
    eth = lb[lb["symbol"] == "ETHUSDT"][keys + [
        "count", "mean_forward_return", "hit_rate_at_zero", "mfe_mae_ratio", "net_after_fee"
    ]].rename(columns={
        "count": "eth_count",
        "mean_forward_return": "eth_mean",
        "hit_rate_at_zero": "eth_hit",
        "mfe_mae_ratio": "eth_ratio",
        "net_after_fee": "eth_net",
    })
    out = btc.merge(eth, on=keys, how="inner")
    if out.empty:
        return out
    out["avg_net"] = (out["btc_net"] + out["eth_net"]) / 2.0
    out["min_net"] = out[["btc_net", "eth_net"]].min(axis=1)
    out["both_pass"] = (
        (out["btc_count"] >= PARETO_MIN_N)
        & (out["eth_count"] >= PARETO_MIN_N)
        & (out["btc_net"] > 0)
        & (out["eth_net"] > 0)
        & (out["btc_hit"] > 0.55)
        & (out["eth_hit"] > 0.55)
        & (out["btc_ratio"] >= 1.0)
        & (out["eth_ratio"] >= 1.0)
    )
    out["one_symbol_only"] = (
        ((out["btc_count"] >= PARETO_MIN_N) & (out["btc_net"] > 0) & (out["btc_hit"] > 0.55) & (out["btc_ratio"] >= 1.0))
        ^ ((out["eth_count"] >= PARETO_MIN_N) & (out["eth_net"] > 0) & (out["eth_hit"] > 0.55) & (out["eth_ratio"] >= 1.0))
    )
    return out.sort_values(["both_pass", "avg_net", "min_net"], ascending=[False, False, False])


def refresh_universe_status() -> int:
    lines = ["# Universe Status", "", f"Last refresh: {_utc_now()}.", "", "## Loaded series (binance)", "",
             "| symbol | tf | first bar | last bar | bars | features | regimes | events | outcomes | leaderboard |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            n, first, last = _read_meta(_proc_path("bars", symbol, tf))
            f_n, _, _ = _read_meta(_proc_path("features", symbol, tf))
            r_n, _, _ = _read_meta(_proc_path("regimes", symbol, tf))
            ev_n, _, _ = _read_meta(_proc_path("events", symbol, tf))
            out_n, _, _ = _read_meta(_proc_path("outcomes", symbol, tf))
            lb_n, _, _ = _read_meta(_proc_path("leaderboard", symbol, tf))
            lines.append(
                f"| {symbol} | {tf} | {_ms_to_str(first)} | {_ms_to_str(last)} | "
                f"{n} | {f_n} | {r_n} | {ev_n} | {out_n} | {lb_n} |"
            )
    lines += [
        "",
        "## Scope",
        "",
        "- Binance only. Bybit / OKX remain out of scope.",
        "- Validation scope: BTCUSDT and ETHUSDT.",
        "- Quality details: `data_layer/reports/quality/latest_summary.md`.",
    ]
    out = REPORTS / "summaries" / "universe_status.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_feature_catalog() -> int:
    lines = ["# Feature Catalog", "", f"Last refresh: {_utc_now()}.",
             "Source: `data_layer/store/processed/features/binance/<SYMBOL>/<TF>.parquet`.", "",
             "Definitions below are shared by BTCUSDT and ETHUSDT on Binance.", "",
             "| feature | description | window |", "|---|---|---|"]
    for spec in FEATURE_SPECS:
        lines.append(f"| {spec.name} | {spec.description} | {spec.window} |")
    out = REPORTS / "summaries" / "feature_catalog.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_regime_summary() -> int:
    lines = ["# Regime Summary", "", f"Last refresh: {_utc_now()}.",
             "Source: `data_layer/store/processed/regimes/binance/<SYMBOL>/<TF>.parquet`.", "",
             "| symbol | tf | last bar | composite | confidence |",
             "|---|---|---|---|---|"]
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            df = _read_df(_proc_path("regimes", symbol, tf))
            if df.empty:
                lines.append(f"| {symbol} | {tf} | - | - | - |")
                continue
            last = df.iloc[-1]
            lines.append(
                f"| {symbol} | {tf} | {_ms_to_str(int(last['ts_open_ms']))} | "
                f"{last['composite_label']} | {last['confidence']} |"
            )
    out = REPORTS / "summaries" / "regime_summary.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_event_catalog() -> int:
    counts: dict[tuple[str, str], dict[str, int]] = {}
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            df = _read_df(_proc_path("events", symbol, tf))
            vc = df["event_type"].value_counts().to_dict() if not df.empty else {}
            counts[(symbol, tf)] = {ev: int(vc.get(ev, 0)) for ev in IMPLEMENTED_EVENT_TYPES}
    lines = ["# Event Catalog", "", f"Last refresh: {_utc_now()}.",
             "Source: `data_layer/store/processed/events/binance/<SYMBOL>/<TF>.parquet`.", "",
             "| event_type | 5m BTC | 5m ETH | 1h BTC | 1h ETH |",
             "|---|---|---|---|---|"]
    for ev in IMPLEMENTED_EVENT_TYPES:
        lines.append(
            f"| {ev} | {counts[('BTCUSDT', '5m')][ev]} | {counts[('ETHUSDT', '5m')][ev]} | "
            f"{counts[('BTCUSDT', '1h')][ev]} | {counts[('ETHUSDT', '1h')][ev]} |"
        )
    lines += ["", "## Notes", ""]
    for ev in IMPLEMENTED_EVENT_TYPES:
        lines.append(f"- `{ev}`: {IMPLEMENTED_DESC[ev]}")
    for ev, reason in SKIPPED_EVENT_TYPES.items():
        lines.append(f"- `{ev}` skipped: {reason}.")
    out = REPORTS / "summaries" / "event_catalog.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


OUTCOME_SUMMARY_TOP_K = 30


def refresh_outcome_summary() -> int:
    lb = _load_leaderboards()
    lines = ["# Outcome Summary", "", f"Last refresh: {_utc_now()}."]
    if lb.empty:
        lines += [
            f"Rows shown only when `n >= {PARETO_MIN_N}` to keep the report compact and aligned with Pareto checks.",
            "", "| symbol | tf | event | h | n | fwd | net | hit | MFE/|MAE| |",
            "|---|---|---|---|---|---|---|---|---|",
            "| - | - | - | - | 0 | - | - | - | - |",
        ]
    else:
        shown_all = lb[lb["count"] >= PARETO_MIN_N]
        total = len(shown_all)
        # Rank by absolute net edge after fees so the most extreme cells
        # surface first, then fall back to deterministic key order on ties.
        if not shown_all.empty:
            shown = shown_all.copy()
            shown["_abs_net"] = shown["net_after_fee"].abs()
            shown = shown.sort_values(
                by=["_abs_net", "symbol", "timeframe", "_h", "event_type"],
                ascending=[False, True, True, True, True],
            ).head(OUTCOME_SUMMARY_TOP_K)
        else:
            shown = shown_all
        lines += [
            f"Rows shown only when `n >= {PARETO_MIN_N}`. Showing top {OUTCOME_SUMMARY_TOP_K} cells by |net| out of {total}; the full table is in `data_layer/store/processed/leaderboard/`.",
            "", "| symbol | tf | event | h | n | fwd | net | hit | MFE/|MAE| |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        if shown.empty:
            lines.append("| - | - | - | - | 0 | - | - | - | - |")
        else:
            for _, r in shown.iterrows():
                hit = "-" if pd.isna(r["hit_rate_at_zero"]) else f"{r['hit_rate_at_zero'] * 100:.0f}%"
                lines.append(
                    f"| {r['symbol']} | {r['timeframe']} | {str(r['event_type']).replace('EV_', '')} | "
                    f"{r['horizon']} | {int(r['count'])} | {_fmt_pct(r['mean_forward_return'])} | "
                    f"{_fmt_pct(r['net_after_fee'])} | {hit} | {_fmt_ratio(r['mfe_mae_ratio'])} |"
                )
    out = REPORTS / "summaries" / "outcome_summary.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_event_leaderboard() -> int:
    lb = _load_leaderboards()
    lines = ["# Event Leaderboard", "", f"Last refresh: {_utc_now()}.",
             f"Top 12 cells by `|sharpe_like|`, requiring `count >= {MIN_COUNT_FOR_RANKING}`.", ""]
    if lb.empty:
        lines.append("No leaderboard rows available.")
    else:
        ranked = lb[lb["count"] >= MIN_COUNT_FOR_RANKING].dropna(subset=["sharpe_like"]).copy()
        ranked = ranked.reindex(ranked["sharpe_like"].abs().sort_values(ascending=False).index).head(12)
        lines += ["| rank | symbol | tf | event | h | n | mean fwd | net | hit | MFE/|MAE| |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(ranked.itertuples(index=False), 1):
            hit = "-" if pd.isna(r.hit_rate_at_zero) else f"{r.hit_rate_at_zero * 100:.0f}%"
            lines.append(
                f"| {i} | {r.symbol} | {r.timeframe} | {str(r.event_type).replace('EV_', '')} | "
                f"{r.horizon} | {int(r.count)} | {_fmt_pct(r.mean_forward_return)} | "
                f"{_fmt_pct(r.net_after_fee)} | {hit} | {_fmt_ratio(r.mfe_mae_ratio)} |"
            )
    out = REPORTS / "leaderboards" / "latest_event_leaderboard.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_pareto_validation() -> int:
    lb = _load_leaderboards()
    pairs = _pair_rows(lb)
    decision = "NO CANDIDATE"
    weakness = "No common BTCUSDT / ETHUSDT cell cleared the net-after-fees threshold."
    best = None
    if not pairs.empty:
        best = pairs.iloc[0]
        if bool(best["both_pass"]):
            decision = "RESEARCH CANDIDATE"
            weakness = "Cross-symbol stability achieved on the best common cell."
        elif pairs["one_symbol_only"].any() or (best["btc_net"] > 0) or (best["eth_net"] > 0):
            decision = "WATCHLIST ONLY"
            weakness = "The best event is not stable across both symbols after fees."
    lines = ["# Pareto Validation (BTCUSDT vs ETHUSDT)", "",
             f"Generated: {_utc_now()}. Binance only. Fee+slippage proxy = {FEE_PCT:.2f}%.", "",
             "## Decision", "", f"**{decision}.**", "",
             f"Rule for `RESEARCH CANDIDATE`: both symbols need `n >= {PARETO_MIN_N}`, positive net after fees, `hit > 55%`, and `MFE/|MAE| >= 1.0`.", ""]
    if best is not None:
        lines += ["## Best common cell", "",
                  "| event | tf | h | BTC n | BTC fwd/net | BTC hit | BTC ratio | ETH n | ETH fwd/net | ETH hit | ETH ratio |",
                  "|---|---|---|---|---|---|---|---|---|---|---|",
                  f"| {best['event_type']} | {best['timeframe']} | {best['horizon']} | "
                  f"{int(best['btc_count'])} | {_fmt_pct(best['btc_mean'])} / {_fmt_pct(best['btc_net'])} | "
                  f"{best['btc_hit'] * 100:.0f}% | {_fmt_ratio(best['btc_ratio'])} | "
                  f"{int(best['eth_count'])} | {_fmt_pct(best['eth_mean'])} / {_fmt_pct(best['eth_net'])} | "
                  f"{best['eth_hit'] * 100:.0f}% | {_fmt_ratio(best['eth_ratio'])} |",
                  "", "## Main weakness", "", weakness]
    else:
        lines += ["## Main weakness", "", weakness]
    out = REPORTS / "summaries" / "pareto_validation.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def _load_stability() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load combined walk-forward and permutation parquets across
    symbols / timeframes. Returns (walk_forward_df, permutation_df).
    """
    base = STORE_ROOT / "processed" / "stability" / "binance"
    wf_rows: list[pd.DataFrame] = []
    pm_rows: list[pd.DataFrame] = []
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            wf_path = base / symbol / f"{tf}__walk_forward.parquet"
            pm_path = base / symbol / f"{tf}__permutation.parquet"
            if wf_path.exists():
                wf_rows.append(pd.read_parquet(wf_path))
            if pm_path.exists():
                pm_rows.append(pd.read_parquet(pm_path))
    wf = pd.concat(wf_rows, ignore_index=True) if wf_rows else pd.DataFrame()
    pm = pd.concat(pm_rows, ignore_index=True) if pm_rows else pd.DataFrame()
    return wf, pm


def refresh_walk_forward_summary() -> int:
    wf, _ = _load_stability()
    lines = ["# Walk-Forward Stability", "", f"Last refresh: {_utc_now()}.",
             "Splits each (symbol, tf, event_type, horizon) cell with "
             f"`n >= {PARETO_MIN_N}` chronologically into 3 folds and reports "
             "per-fold net after taker (Tier T) and maker (Tier M) friction. "
             "A cell is `STABLE` if every fold's net has the same sign as "
             "the full-sample net.", ""]
    if wf.empty:
        lines.append("No stability data available. Run `python -m data_layer.scripts.cli stability-validation`.")
    else:
        eligible = wf[wf["n_complete"] >= PARETO_MIN_N].copy()
        # Top 20 ranked by maker net (descending) so the most attractive
        # cells under Profile A-Maker surface first.
        eligible = eligible.sort_values(
            ["full_net_maker", "n_complete"], ascending=[False, False]
        ).head(20)
        lines += [
            f"Showing top 20 cells by `full_net_maker` (out of {int((wf['n_complete'] >= PARETO_MIN_N).sum())} with `n >= {PARETO_MIN_N}`).",
            "",
            "| symbol | tf | event | h | n | net T | net M | T sign-stable | M sign-stable |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for _, r in eligible.iterrows():
            ev = str(r["event_type"]).replace("EV_", "")
            t_stable = "yes" if bool(r["sign_stable"]) else f"{int(r['folds_same_sign'])}/3"
            m_stable = "yes" if bool(r["sign_stable_maker"]) else f"{int(r['folds_same_sign_maker'])}/3"
            lines.append(
                f"| {r['symbol']} | {r['timeframe']} | {ev} | {r['horizon']} | "
                f"{int(r['n_complete'])} | {_fmt_pct(r['full_net'])} | "
                f"{_fmt_pct(r['full_net_maker'])} | {t_stable} | {m_stable} |"
            )
    out = REPORTS / "summaries" / "walk_forward.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_permutation_summary() -> int:
    _, pm = _load_stability()
    lines = ["# Permutation Test", "", f"Last refresh: {_utc_now()}.",
             "Bootstrap test: for each cell with `n >= " f"{PARETO_MIN_N}` we draw 1000 random samples of the "
             "same size from the underlying bar-level forward-return universe at the matching horizon "
             "and compute the two-tailed p-value `(1 + #{|perm_mean| >= |obs_mean|}) / (n_perms + 1)`. "
             "A cell is `PASS` when `p_value <= 0.05`.", ""]
    if pm.empty:
        lines.append("No stability data available. Run `python -m data_layer.scripts.cli stability-validation`.")
    else:
        eligible = pm[pm["n_complete"] >= PARETO_MIN_N].copy()
        # Top 20 ranked by p_value ascending (most significant first).
        eligible = eligible.sort_values(["p_value", "n_complete"], ascending=[True, False]).head(20)
        n_pass = int((pm["verdict"] == "PASS").sum())
        n_total = int((pm["n_complete"] >= PARETO_MIN_N).sum())
        lines += [
            f"Showing top 20 cells by p-value (out of {n_total}; {n_pass} cells PASS at p<=0.05).",
            "",
            "| symbol | tf | event | h | n | obs net T | obs net M | p-value | verdict |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for _, r in eligible.iterrows():
            ev = str(r["event_type"]).replace("EV_", "")
            p = "-" if pd.isna(r["p_value"]) else f"{r['p_value']:.3f}"
            lines.append(
                f"| {r['symbol']} | {r['timeframe']} | {ev} | {r['horizon']} | "
                f"{int(r['n_complete'])} | {_fmt_pct(r['obs_net'])} | "
                f"{_fmt_pct(r['obs_net_maker'])} | {p} | {r['verdict']} |"
            )
    out = REPORTS / "summaries" / "permutation_test.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


# Permutation p-value thresholds per execution tier. Tier T uses the
# strict 0.05; Tier M is relaxed to 0.10 while only 365 days of data
# are available (revisit when the window is expanded to >= 3 years).
P_VALUE_PASS_TIER_T = 0.05
P_VALUE_PASS_TIER_M = 0.10

# Maker-tier round-trip friction (Profile A-Maker). Mirrors
# `data_layer.process.stability.FEE_PCT_MAKER` so the candidate report
# uses the same number as the underlying parquet.
FEE_PCT_MAKER = 0.10


def refresh_research_candidates_summary() -> int:
    """One-stop list of cells that pass every gate at once.

    Codex researcher mode reads this file first; if a row appears here,
    the cell already cleared n>=80, walk-forward sign stability, and
    the permutation p-value threshold for the matching tier. Cells
    with cross-symbol pairing are surfaced first.
    """
    wf, pm = _load_stability()
    lines = ["# Research Candidates", "", f"Last refresh: {_utc_now()}.",
             "Cells that pass every stability gate at once. Tier T uses "
             f"`p <= {P_VALUE_PASS_TIER_T:.2f}`; Tier M uses "
             f"`p <= {P_VALUE_PASS_TIER_M:.2f}` (relaxed while only "
             "365 days of data are available). All rows already require "
             f"`n >= {PARETO_MIN_N}` and walk-forward sign stability for "
             "the matching tier. Source: `walk_forward.md` + "
             "`permutation_test.md`.", ""]
    if wf.empty or pm.empty:
        lines.append("No stability data available. Run `python -m data_layer.scripts.cli stability-validation`.")
        out = REPORTS / "summaries" / "research_candidates.md"
        _write_capped(out, lines)
        print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
        return 0

    key = ["symbol", "timeframe", "event_type", "horizon"]
    merged = wf.merge(pm, on=key, how="inner", suffixes=("", "_pm"))

    eligible_t = merged[
        (merged["n_complete"] >= PARETO_MIN_N)
        & (merged["sign_stable"])
        & (merged["full_net"] > 0)
        & (merged["p_value"] <= P_VALUE_PASS_TIER_T)
    ].copy()
    eligible_m = merged[
        (merged["n_complete"] >= PARETO_MIN_N)
        & (merged["sign_stable_maker"])
        & (merged["full_net_maker"] > 0)
        & (merged["p_value"] <= P_VALUE_PASS_TIER_M)
    ].copy()

    def _emit_section(title: str, df: pd.DataFrame, net_col: str) -> list[str]:
        section = [f"## {title}", ""]
        if df.empty:
            section += ["None.", ""]
            return section
        df = df.sort_values([net_col, "n_complete"], ascending=[False, False])
        section += [
            "| symbol | tf | event | h | n | net | p-value |",
            "|---|---|---|---|---|---|---|",
        ]
        for _, r in df.iterrows():
            ev = str(r["event_type"]).replace("EV_", "")
            p = "-" if pd.isna(r["p_value"]) else f"{r['p_value']:.3f}"
            section.append(
                f"| {r['symbol']} | {r['timeframe']} | {ev} | {r['horizon']} | "
                f"{int(r['n_complete'])} | {_fmt_pct(r[net_col])} | {p} |"
            )
        section.append("")
        return section

    # Cross-symbol joint pass: same (tf, event, h) cell passes for both
    # BTC and ETH at the same tier. Surface these first because the
    # auditor's Pareto gate is hardest to clear.
    def _cross_symbol(df: pd.DataFrame, net_col: str) -> pd.DataFrame:
        if df.empty:
            return df
        btc = df[df["symbol"] == "BTCUSDT"]
        eth = df[df["symbol"] == "ETHUSDT"]
        join_keys = ["timeframe", "event_type", "horizon"]
        joined = btc.merge(eth, on=join_keys, how="inner", suffixes=("_btc", "_eth"))
        return joined

    cross_t = _cross_symbol(eligible_t, "full_net")
    cross_m = _cross_symbol(eligible_m, "full_net_maker")

    lines += ["## Cross-symbol Pareto + stability (highest grade)", ""]
    if cross_t.empty and cross_m.empty:
        lines += [
            "None at the current window. The auditor cross-symbol "
            "Pareto gate is currently empty for both tiers.",
            "",
        ]
    else:
        lines += [
            "| tier | tf | event | h | BTC n | BTC net | BTC p | ETH n | ETH net | ETH p |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for _, r in cross_t.iterrows():
            ev = str(r["event_type"]).replace("EV_", "")
            lines.append(
                f"| T | {r['timeframe']} | {ev} | {r['horizon']} | "
                f"{int(r['n_complete_btc'])} | {_fmt_pct(r['full_net_btc'])} | {r['p_value_btc']:.3f} | "
                f"{int(r['n_complete_eth'])} | {_fmt_pct(r['full_net_eth'])} | {r['p_value_eth']:.3f} |"
            )
        for _, r in cross_m.iterrows():
            ev = str(r["event_type"]).replace("EV_", "")
            lines.append(
                f"| M | {r['timeframe']} | {ev} | {r['horizon']} | "
                f"{int(r['n_complete_btc'])} | {_fmt_pct(r['full_net_maker_btc'])} | {r['p_value_btc']:.3f} | "
                f"{int(r['n_complete_eth'])} | {_fmt_pct(r['full_net_maker_eth'])} | {r['p_value_eth']:.3f} |"
            )
        lines.append("")

    lines += _emit_section(
        f"Tier T single-symbol candidates (`p <= {P_VALUE_PASS_TIER_T:.2f}`)",
        eligible_t,
        "full_net",
    )
    lines += _emit_section(
        f"Tier M single-symbol candidates (`p <= {P_VALUE_PASS_TIER_M:.2f}`)",
        eligible_m,
        "full_net_maker",
    )

    out = REPORTS / "summaries" / "research_candidates.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_all_summaries() -> int:
    refresh_universe_status()
    refresh_feature_catalog()
    refresh_regime_summary()
    refresh_event_catalog()
    refresh_outcome_summary()
    refresh_event_leaderboard()
    refresh_pareto_validation()
    refresh_walk_forward_summary()
    refresh_permutation_summary()
    refresh_research_candidates_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(refresh_all_summaries())
