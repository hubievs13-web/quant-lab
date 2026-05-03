"""Regenerate small Codex-readable markdown summaries.

Phase 2 emitted only `summaries/universe_status.md`. Phase 3 adds:
- `summaries/feature_catalog.md`
- `summaries/regime_summary.md`

All reports stay <= 5 KB (verified by an assert at write time).
"""
from __future__ import annotations

import datetime as dt
from collections import OrderedDict
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

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
    lines.append("## Pending phases")
    lines.append("")
    lines.append("- Phase 4 (events + outcomes + leaderboard): pending approval")
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
        "- `funding_rate_zscore_30d`, `oi_zscore_30d`: require >= 7 days of "
        "history; smoke 5m window is 7 days (still sparse), so 5m yields 0 valid."
    )
    lines.append(
        "- `basis_bp`: mark/index series not ingested in Phase 2/3; populated in "
        "Phase 4+."
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
        "- `basis_regime` is `insufficient_data` everywhere in Phase 2/3 (no "
        "mark/index series ingested yet)."
    )
    lines.append(
        "- `crowding_regime` is `balanced` whenever `top_trader_position_ratio` "
        "is present; richer crowded_long / crowded_short labels are Phase 4."
    )
    lines.append(
        "- 5m `funding_regime` insufficient bars (~last 2 days) reflect missing "
        "May-2026 monthly funding zip; arrives once month rolls."
    )

    out = REPORTS / "summaries" / "regime_summary.md"
    _write_capped(out, lines)
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def refresh_all_summaries() -> int:
    refresh_universe_status()
    refresh_feature_catalog()
    refresh_regime_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(refresh_all_summaries())
