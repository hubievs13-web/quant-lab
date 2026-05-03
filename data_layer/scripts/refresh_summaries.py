"""Regenerate small Codex-readable markdown summaries.

Phase 2 emitted only `summaries/universe_status.md`. Phase 3 added
`summaries/feature_catalog.md` and `summaries/regime_summary.md`.
Phase 4 adds:
- `summaries/event_catalog.md`
- `summaries/outcome_summary.md`
- `leaderboards/latest_event_leaderboard.md`

All reports stay <= 5 KB (verified at write time).
"""
from __future__ import annotations

import datetime as dt
from collections import OrderedDict
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from data_layer.process.events import IMPLEMENTED_EVENT_TYPES, SKIPPED_EVENT_TYPES, THRESH as EVENT_THRESH
from data_layer.process.features import FEATURE_SPECS

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
REPORTS = REPO_ROOT / "data_layer" / "reports"
SYMBOL = "BTCUSDT"
TIMEFRAMES = ("5m", "1h")
REPORT_CAP_BYTES = 5 * 1024


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")


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
        raise RuntimeError(
            f"Report {path} exceeds 5 KB cap ({len(text)} bytes). Tighten content."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# ---------- universe_status.md (Phase 2 + 3 update) ------------------

def refresh_universe_status() -> int:
    lines: list[str] = []
    lines.append("# Universe Status")
    lines.append("")
    lines.append(f"Last refresh: {_utc_now()}.")
    lines.append("")
    lines.append("## Loaded series (binance, BTCUSDT)")
    lines.append("")
    lines.append("| timeframe | first bar | last bar | rows |")
    lines.append("|---|---|---|---|")
    for tf in TIMEFRAMES:
        n, first, last = _read_meta(
            STORE_ROOT / "processed/bars/binance" / SYMBOL / f"{tf}.parquet"
        )
        lines.append(f"| {tf} | {_ms_to_str(first)} | {_ms_to_str(last)} | {n} |")

    lines.append("")
    lines.append("## Phase 3 outputs (binance, BTCUSDT)")
    lines.append("")
    lines.append("| timeframe | features rows | regimes rows |")
    lines.append("|---|---|---|")
    for tf in TIMEFRAMES:
        f_n, _, _ = _read_meta(
            STORE_ROOT / "processed/features/binance" / SYMBOL / f"{tf}.parquet"
        )
        r_n, _, _ = _read_meta(
            STORE_ROOT / "processed/regimes/binance" / SYMBOL / f"{tf}.parquet"
        )
        lines.append(f"| {tf} | {f_n} | {r_n} |")

    lines.append("")
    lines.append("## Derivatives")
    lines.append("")
    lines.append("- Funding rate: see `data_layer/reports/quality/latest_summary.md`.")
    lines.append("- Open Interest (5-min metrics): see `data_layer/reports/quality/latest_summary.md`.")
    lines.append("")
    lines.append("## Phase 4 outputs (binance, BTCUSDT)")
    lines.append("")
    lines.append("| timeframe | events rows | outcomes rows | leaderboard rows |")
    lines.append("|---|---|---|---|")
    for tf in TIMEFRAMES:
        ev_n, _, _ = _read_meta(
            STORE_ROOT / "processed/events/binance" / SYMBOL / f"{tf}.parquet"
        )
        out_n, _, _ = _read_meta(
            STORE_ROOT / "processed/outcomes/binance" / SYMBOL / f"{tf}.parquet"
        )
        lb_n, _, _ = _read_meta(
            STORE_ROOT / "processed/leaderboard/binance" / SYMBOL / f"{tf}.parquet"
        )
        lines.append(f"| {tf} | {ev_n} | {out_n} | {lb_n} |")
    lines.append("")
    lines.append("## Pending phases")
    lines.append("")
    lines.append("- Phase 5 (Bybit + OKX): pending approval")
    lines.append("- Phase 6 (hypothesis seed briefs): pending approval")
    lines.append("- Phase 7 (liquidations + book): deferred")
    lines.append("")
    lines.append("Read order for Codex / Devin: see `data_layer/README.md`.")

    out = REPORTS / "summaries" / "universe_status.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


# ---------- feature_catalog.md (Phase 3) -----------------------------

def _features_path(tf: str) -> Path:
    return STORE_ROOT / "processed/features/binance" / SYMBOL / f"{tf}.parquet"


def refresh_feature_catalog() -> int:
    coverage: dict[str, dict[str, tuple[int, int]]] = {}
    for tf in TIMEFRAMES:
        p = _features_path(tf)
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        coverage[tf] = {
            spec.name: (int(df[spec.name].notna().sum()), len(df))
            for spec in FEATURE_SPECS
            if spec.name in df.columns
        }

    lines: list[str] = []
    lines.append("# Feature Catalog")
    lines.append("")
    lines.append(f"Last refresh: {_utc_now()}.")
    lines.append(
        "Source: `data_layer/store/processed/features/binance/<SYMBOL>/<TF>.parquet`."
    )
    lines.append(
        "Defs in `data_layer/config/features.yaml` and "
        "`data_layer/process/features.py`."
    )
    lines.append("")
    lines.append("Anti-lookahead: every feature for bar i uses only bar i and earlier.")
    lines.append("")
    lines.append("## Features (binance, BTCUSDT)")
    lines.append("")
    lines.append("| feature | description | window | 5m non-null | 1h non-null |")
    lines.append("|---|---|---|---|---|")
    for spec in FEATURE_SPECS:
        c5 = coverage.get("5m", {}).get(spec.name)
        c1 = coverage.get("1h", {}).get(spec.name)
        f5 = f"{c5[0]}/{c5[1]}" if c5 else "-"
        f1 = f"{c1[0]}/{c1[1]}" if c1 else "-"
        lines.append(f"| {spec.name} | {spec.description} | {spec.window} | {f5} | {f1} |")

    lines.append("")
    lines.append("## Insufficient_data notes")
    lines.append("")
    lines.append(
        "- `funding_rate_zscore_30d`, `oi_zscore_30d`: need >= 7 days of "
        "history before producing values; null on the warm-up tail of each window."
    )
    lines.append(
        "- `basis_bp` is computed from mark + index price klines fetched from "
        "data.binance.vision (futures/um daily archives)."
    )
    lines.append(
        "- crowding cols come from raw OI metrics with 60-min TTL (asof backward)."
    )

    out = REPORTS / "summaries" / "feature_catalog.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


# ---------- regime_summary.md (Phase 3) ------------------------------

REGIME_COLS = (
    "trend_regime",
    "vol_regime",
    "funding_regime",
    "basis_regime",
    "crowding_regime",
    "liquidity_regime",
)
REGIME_LABEL = {
    "trend_regime": "Trend",
    "vol_regime": "Vol",
    "funding_regime": "Funding",
    "basis_regime": "Basis",
    "crowding_regime": "Crowding",
    "liquidity_regime": "Liquidity",
}
DESIRED_ORDER = {
    "trend_regime": ["up_trend", "chop", "down_trend", "insufficient_data"],
    "vol_regime": ["low", "mid", "high", "insufficient_data"],
    "funding_regime": ["pos_extreme", "pos_normal", "flat", "neg_normal", "neg_extreme", "insufficient_data"],
    "basis_regime": ["premium_rich", "neutral", "discount_rich", "insufficient_data"],
    "crowding_regime": ["balanced", "insufficient_data"],
    "liquidity_regime": ["thin", "normal", "thick", "insufficient_data"],
}


def _regimes_path(tf: str) -> Path:
    return STORE_ROOT / "processed/regimes/binance" / SYMBOL / f"{tf}.parquet"


def _ordered_counts(series: pd.Series, col: str) -> list[tuple[str, int]]:
    vc = series.value_counts(dropna=False).to_dict()
    out = []
    seen = set()
    for k in DESIRED_ORDER.get(col, []):
        if k in vc:
            out.append((k, int(vc[k])))
            seen.add(k)
    for k, v in vc.items():
        if k not in seen:
            out.append((str(k), int(v)))
    return out


def refresh_regime_summary() -> int:
    data: dict[str, pd.DataFrame] = {}
    for tf in TIMEFRAMES:
        p = _regimes_path(tf)
        if p.exists():
            data[tf] = pd.read_parquet(p)

    lines: list[str] = []
    lines.append("# Regime Summary")
    lines.append("")
    lines.append(f"Last refresh: {_utc_now()}.")
    lines.append(
        "Source: `data_layer/store/processed/regimes/binance/<SYMBOL>/<TF>.parquet`."
    )
    lines.append(
        "Thresholds: `data_layer/config/regimes.yaml` and "
        "`data_layer/process/regimes.py:THRESH`."
    )
    lines.append("")

    # Latest bar
    lines.append("## Latest bar")
    lines.append("")
    lines.append("| timeframe | last bar | composite | confidence |")
    lines.append("|---|---|---|---|")
    for tf, df in data.items():
        last = df.iloc[-1]
        ts = _ms_to_str(int(last["ts_open_ms"]))
        lines.append(
            f"| {tf} | {ts} | {last['composite_label']} | {last['confidence']} |"
        )
    lines.append("")

    # Per-component distribution table
    for tf, df in data.items():
        lines.append(f"## Distribution ({tf}, {len(df)} bars)")
        lines.append("")
        lines.append("| component | label | count | share |")
        lines.append("|---|---|---|---|")
        for col in REGIME_COLS:
            counts = _ordered_counts(df[col], col)
            total = sum(c for _, c in counts) or 1
            for label, c in counts:
                share = f"{(100.0 * c / total):.1f}%"
                lines.append(f"| {REGIME_LABEL[col]} | {label} | {c} | {share} |")
        lines.append("")

    # Notes
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- `basis_regime` now uses real mark/index ingest from "
        "data.binance.vision; `discount_rich` flags index > mark by enough bp."
    )
    lines.append(
        "- `crowding_regime` is `balanced` whenever `top_trader_position_ratio` "
        "is present; richer crowded_long / crowded_short labels still pending."
    )
    lines.append(
        "- Residual `insufficient_data` in `funding_regime` reflects the tail "
        "of the window where the next monthly funding zip is not yet on the CDN."
    )

    out = REPORTS / "summaries" / "regime_summary.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


# ---------- event_catalog.md (Phase 4) -------------------------------

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


def _events_path(tf: str) -> Path:
    return STORE_ROOT / "processed/events/binance" / SYMBOL / f"{tf}.parquet"


def refresh_event_catalog() -> int:
    counts: dict[str, dict[str, int]] = {}
    for tf in TIMEFRAMES:
        p = _events_path(tf)
        if not p.exists():
            counts[tf] = {}
            continue
        df = pd.read_parquet(p)
        if df.empty:
            counts[tf] = {ev: 0 for ev in IMPLEMENTED_EVENT_TYPES}
        else:
            vc = df["event_type"].value_counts().to_dict()
            counts[tf] = {ev: int(vc.get(ev, 0)) for ev in IMPLEMENTED_EVENT_TYPES}

    lines: list[str] = []
    lines.append("# Event Catalog")
    lines.append("")
    lines.append(f"Last refresh: {_utc_now()}.")
    lines.append(
        "Source: `data_layer/store/processed/events/binance/<SYMBOL>/<TF>.parquet`."
    )
    lines.append(
        "Defs in `data_layer/config/events.yaml` and "
        "`data_layer/process/events.py:THRESH`."
    )
    lines.append("")
    lines.append(
        "Anti-lookahead: each event uses only features at bar i; "
        "first-cross only (False -> True transition)."
    )
    lines.append("")
    lines.append("## Implemented events (binance, BTCUSDT)")
    lines.append("")
    lines.append("| event_type | description | 5m count | 1h count |")
    lines.append("|---|---|---|---|")
    for ev in IMPLEMENTED_EVENT_TYPES:
        c5 = counts.get("5m", {}).get(ev, 0)
        c1 = counts.get("1h", {}).get(ev, 0)
        lines.append(f"| {ev} | {IMPLEMENTED_DESC[ev]} | {c5} | {c1} |")

    lines.append("")
    lines.append("## Skipped events (insufficient_data)")
    lines.append("")
    lines.append("| event_type | reason |")
    lines.append("|---|---|")
    for ev, reason in SKIPPED_EVENT_TYPES.items():
        lines.append(f"| {ev} | {reason} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- `event_strength` is in absolute z-score units where applicable; "
        "for fallback paths it is normalised to the same magnitude scale."
    )
    lines.append(
        "- `context_regime` on each event row is the `composite_label` from "
        "`processed/regimes` at the same `ts_open_ms`."
    )

    out = REPORTS / "summaries" / "event_catalog.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


# ---------- outcome_summary.md (Phase 4) -----------------------------

def _outcomes_path(tf: str) -> Path:
    return STORE_ROOT / "processed/outcomes/binance" / SYMBOL / f"{tf}.parquet"


def _leaderboard_path(tf: str) -> Path:
    return STORE_ROOT / "processed/leaderboard/binance" / SYMBOL / f"{tf}.parquet"


def _fmt_pct(v: float) -> str:
    if pd.isna(v):
        return "-"
    return f"{v:+.2f}%"


def _fmt_ratio(v: float) -> str:
    if pd.isna(v):
        return "-"
    return f"{v:.2f}"


def refresh_outcome_summary() -> int:
    lines: list[str] = []
    lines.append("# Outcome Summary")
    lines.append("")
    lines.append(f"Last refresh: {_utc_now()}.")
    lines.append(
        "Source: `data_layer/store/processed/outcomes/binance/<SYMBOL>/<TF>.parquet`."
    )
    lines.append(
        "Anchor: bar AFTER event (next-bar entry; no same-bar contamination)."
    )
    lines.append(
        "Counts are complete only. Rows with n < 10 omitted to keep the "
        "report compact; full table is in the leaderboard parquet."
    )
    lines.append("")

    for tf in TIMEFRAMES:
        p = _leaderboard_path(tf)
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if df.empty:
            continue
        lines.append(f"## {tf} (binance, BTCUSDT)")
        lines.append("")
        lines.append(
            "| event | h | n | fwd | hit | MFE | MAE |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        df = df.copy()
        df["_h"] = df["horizon"].str.replace("h+", "", regex=False).astype(int)
        df = df[df["count"] >= 10].sort_values(["event_type", "_h"])
        for _, r in df.iterrows():
            n = int(r["count"])
            hit = (
                f"{r['hit_rate_at_zero'] * 100:.0f}%"
                if pd.notna(r["hit_rate_at_zero"]) else "-"
            )
            ev = str(r["event_type"]).replace("EV_", "")
            lines.append(
                f"| {ev} | {r['horizon']} | {n} | "
                f"{_fmt_pct(r['mean_forward_return'])} | {hit} | "
                f"{_fmt_pct(r['median_mfe'])} | {_fmt_pct(r['median_mae'])} |"
            )
        lines.append("")

    lines.append("## Reading guide")
    lines.append("")
    lines.append(
        "- `mean fwd` = mean of `forward_return_pct` over complete outcomes."
    )
    lines.append(
        "- `hit>0` = share of complete outcomes with positive forward_return."
    )
    lines.append(
        "- Smoke samples are tiny; `n < 30` should be treated as descriptive only."
    )

    out = REPORTS / "summaries" / "outcome_summary.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


# ---------- leaderboards/latest_event_leaderboard.md (Phase 4) -------

MIN_COUNT_FOR_RANKING = 30
TOP_K = 12


def refresh_event_leaderboard() -> int:
    rows: list[dict] = []
    for tf in TIMEFRAMES:
        p = _leaderboard_path(tf)
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if df.empty:
            continue
        df = df.copy()
        df["timeframe"] = tf
        rows.append(df)
    if not rows:
        merged = pd.DataFrame()
    else:
        merged = pd.concat(rows, ignore_index=True)

    lines: list[str] = []
    lines.append("# Event Leaderboard")
    lines.append("")
    lines.append(f"Last refresh: {_utc_now()}.")
    lines.append(
        "Source: `data_layer/store/processed/leaderboard/binance/<SYMBOL>/<TF>.parquet`."
    )
    lines.append(
        f"Ranking: top {TOP_K} (event_type, tf, horizon) cells by `sharpe_like`, "
        f"requiring `count >= {MIN_COUNT_FOR_RANKING}`."
    )
    lines.append("")

    if not merged.empty:
        ranked = merged[merged["count"] >= MIN_COUNT_FOR_RANKING].copy()
        ranked = ranked.dropna(subset=["sharpe_like"])
        ranked = ranked.reindex(
            ranked["sharpe_like"].abs().sort_values(ascending=False).index
        ).head(TOP_K)
        if ranked.empty:
            lines.append("No event-cell met the minimum sample requirement.")
        else:
            lines.append(
                "| rank | event_type | tf | horizon | n | mean fwd | hit>0 | sharpe | MFE/|MAE| |"
            )
            lines.append("|---|---|---|---|---|---|---|---|---|")
            for i, r in enumerate(ranked.itertuples(index=False), 1):
                hit = (
                    f"{r.hit_rate_at_zero * 100:.0f}%"
                    if pd.notna(r.hit_rate_at_zero) else "-"
                )
                lines.append(
                    f"| {i} | {r.event_type} | {r.timeframe} | {r.horizon} | "
                    f"{int(r.count)} | {_fmt_pct(r.mean_forward_return)} | {hit} | "
                    f"{_fmt_ratio(r.sharpe_like)} | {_fmt_ratio(r.mfe_mae_ratio)} |"
                )
            lines.append("")

    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- History window: 30d (5m) / 180d (1h); cells with n<30 are excluded "
        "from this ranking but still present in the leaderboard parquet."
    )
    lines.append(
        "- This is a descriptive scan, NOT a verdict. No hypothesis is generated."
    )
    lines.append(
        "- Direction split (long-side vs short-side) is Phase 5+; current view is long-side only."
    )

    out = REPORTS / "leaderboards" / "latest_event_leaderboard.md"
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
    return 0


if __name__ == "__main__":
    raise SystemExit(refresh_all_summaries())
