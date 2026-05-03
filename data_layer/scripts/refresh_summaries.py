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


def refresh_outcome_summary() -> int:
    lb = _load_leaderboards()
    lines = ["# Outcome Summary", "", f"Last refresh: {_utc_now()}.",
             f"Rows shown only when `n >= {PARETO_MIN_N}` to keep the report compact and aligned with Pareto checks.",
             "", "| symbol | tf | event | h | n | fwd | net | hit | MFE/|MAE| |",
             "|---|---|---|---|---|---|---|---|---|"]
    if lb.empty:
        lines.append("| - | - | - | - | 0 | - | - | - | - |")
    else:
        shown = lb[lb["count"] >= PARETO_MIN_N].sort_values(["symbol", "timeframe", "_h", "event_type"])
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


def refresh_all_summaries() -> int:
    refresh_universe_status()
    refresh_feature_catalog()
    refresh_regime_summary()
    refresh_event_catalog()
    refresh_outcome_summary()
    refresh_event_leaderboard()
    refresh_pareto_validation()
    return 0


if __name__ == "__main__":
    raise SystemExit(refresh_all_summaries())
