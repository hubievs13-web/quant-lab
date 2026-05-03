"""Data quality checks (Phase 2 minimal).

Per (symbol, timeframe), measures:
- expected_bars (full-day count vs the smoke window)
- received_bars
- missing_bars
- duplicate_bars (duplicate ts_open_ms in raw)
- out_of_order_rows
- funding_rows_received
- oi_gap_max_minutes

Writes one JSON per (symbol, tf, day) under `store/quality/...` plus
the markdown roll-up at `data_layer/reports/quality/latest_summary.md`
(<= 5 KB).
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

TF_TO_SECONDS = {"5m": 300, "1h": 3600}


def _bars_full_day_count(timeframe: str) -> int:
    return 86400 // TF_TO_SECONDS[timeframe]


def _read_concat(dir_: Path) -> pd.DataFrame:
    if not dir_.exists():
        return pd.DataFrame()
    files = sorted(dir_.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pq.read_table(p).to_pandas() for p in files], ignore_index=True)


def _series_quality(
    bars_df: pd.DataFrame, timeframe: str, day_list: list[dt.date]
) -> dict:
    expected = _bars_full_day_count(timeframe) * len(day_list)
    received = int(len(bars_df))
    duplicates = int(bars_df["ts_open_ms"].duplicated().sum()) if received else 0
    if received:
        sorted_ts = bars_df["ts_open_ms"].sort_values().reset_index(drop=True)
        out_of_order = int(
            (bars_df["ts_open_ms"].reset_index(drop=True) != sorted_ts).sum()
        )
        deduped = int(bars_df["ts_open_ms"].drop_duplicates().shape[0])
    else:
        out_of_order = 0
        deduped = 0
    missing = max(expected - deduped, 0)
    return {
        "expected_bars": expected,
        "received_bars": received,
        "deduped_bars": deduped,
        "missing_bars": missing,
        "duplicate_bars": duplicates,
        "out_of_order_rows": out_of_order,
        "first_ts_ms": int(bars_df["ts_open_ms"].min()) if received else None,
        "last_ts_ms": int(bars_df["ts_open_ms"].max()) if received else None,
    }


def _funding_quality(funding_df: pd.DataFrame, window_days: int) -> dict:
    received = int(len(funding_df))
    expected_per_day = 24 // 8  # 8h interval -> 3 settles/day
    expected = expected_per_day * window_days
    return {
        "funding_rows_received": received,
        "funding_rows_expected_in_window": expected,
        "first_settle_ms": int(funding_df["ts_settle_ms"].min()) if received else None,
        "last_settle_ms": int(funding_df["ts_settle_ms"].max()) if received else None,
    }


def _oi_quality(oi_df: pd.DataFrame) -> dict:
    if oi_df.empty:
        return {
            "oi_rows_received": 0,
            "oi_gap_max_minutes": None,
            "oi_first_ts_ms": None,
            "oi_last_ts_ms": None,
        }
    s = oi_df["ts_ms"].sort_values().reset_index(drop=True)
    diffs_ms = s.diff().dropna()
    max_gap_minutes = float(diffs_ms.max()) / 60000.0 if not diffs_ms.empty else None
    return {
        "oi_rows_received": int(len(oi_df)),
        "oi_gap_max_minutes": max_gap_minutes,
        "oi_first_ts_ms": int(s.iloc[0]),
        "oi_last_ts_ms": int(s.iloc[-1]),
    }


def _status(bars_q: dict) -> str:
    received = bars_q["deduped_bars"]
    expected = bars_q["expected_bars"]
    if expected == 0:
        return "yellow"
    ratio = received / expected
    if ratio >= 0.99 and bars_q["duplicate_bars"] == 0 and bars_q["out_of_order_rows"] == 0:
        return "green"
    if ratio >= 0.95:
        return "yellow"
    return "red"


def run_quality_smoke(
    *,
    repo_root: Path,
    store_root: Path,
    symbols: list[str],
    series: list[tuple[str, int]],  # (timeframe, n_days)
    funding_window_days: int,
    oi_window_days: int,
) -> dict:
    """Compute QC, write per-day JSONs, write markdown roll-up. Returns
    a dict suitable for further use (e.g., universe_status report).
    """
    out: dict = {}
    md_lines: list[str] = []
    md_lines.append("# Data Layer Quality Report (latest)")
    md_lines.append("")
    md_lines.append(f"Generated: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    md_lines.append("Source: Binance USD-M futures via `data.binance.vision` (public CDN).")
    md_lines.append("")
    md_lines.append("## OHLCV (per series)")
    md_lines.append("")
    md_lines.append(
        "| symbol | tf | days | expected | received | dedup | missing | duplicates | "
        "out-of-order | status |"
    )
    md_lines.append("|---|---|---|---|---|---|---|---|---|---|")

    for symbol in symbols:
        out.setdefault(symbol, {})
        for tf, n_days in series:
            raw_dir = store_root / "raw/binance/ohlcv" / symbol / tf
            bars = _read_concat(raw_dir)
            today = dt.datetime.now(dt.UTC).date()
            day_list = [today - dt.timedelta(days=1 + i) for i in range(n_days)]
            q = _series_quality(bars, tf, day_list)
            q["status"] = _status(q)
            out[symbol].setdefault("ohlcv", {})[tf] = q
            md_lines.append(
                f"| {symbol} | {tf} | {n_days} | {q['expected_bars']} | "
                f"{q['received_bars']} | {q['deduped_bars']} | {q['missing_bars']} | "
                f"{q['duplicate_bars']} | {q['out_of_order_rows']} | {q['status']} |"
            )

            qjson_dir = store_root / "quality" / "binance" / symbol / tf
            qjson_dir.mkdir(parents=True, exist_ok=True)
            (qjson_dir / f"{today}.json").write_text(json.dumps(q, indent=2) + "\n")

        funding = _read_concat(store_root / "raw/binance/funding" / symbol)
        f_q = _funding_quality(funding, funding_window_days)
        out[symbol]["funding"] = f_q

        oi = _read_concat(store_root / "raw/binance/oi" / symbol)
        oi_q = _oi_quality(oi)
        out[symbol]["oi"] = oi_q

        for kind, col in (("mark", "mark_close"), ("index", "index_close")):
            tf_rows: dict[str, int] = {}
            for tf, _n_days in series:
                d = store_root / f"raw/binance/{kind}" / symbol / tf
                df = _read_concat(d)
                tf_rows[tf] = int(len(df))
            out[symbol].setdefault("mark_index", {})[kind] = tf_rows

    md_lines.append("")
    md_lines.append("## Funding")
    md_lines.append("")
    md_lines.append("| symbol | rows received | rows expected (~) | first settle (ms) | last settle (ms) |")
    md_lines.append("|---|---|---|---|---|")
    for symbol in symbols:
        f = out[symbol]["funding"]
        md_lines.append(
            f"| {symbol} | {f['funding_rows_received']} | "
            f"{f['funding_rows_expected_in_window']} | {f['first_settle_ms']} | "
            f"{f['last_settle_ms']} |"
        )

    md_lines.append("")
    md_lines.append("## Mark / Index price klines")
    md_lines.append("")
    md_lines.append("| symbol | series | mark rows | index rows |")
    md_lines.append("|---|---|---|---|")
    for symbol in symbols:
        mi = out[symbol].get("mark_index", {})
        mark_rows = mi.get("mark", {})
        index_rows = mi.get("index", {})
        for tf, _n_days in series:
            md_lines.append(
                f"| {symbol} | {tf} | {mark_rows.get(tf, 0)} | {index_rows.get(tf, 0)} |"
            )

    md_lines.append("")
    md_lines.append("## Open Interest (5-minute granularity)")
    md_lines.append("")
    md_lines.append("| symbol | rows received | max gap (minutes) | first ts (ms) | last ts (ms) |")
    md_lines.append("|---|---|---|---|---|")
    for symbol in symbols:
        oq = out[symbol]["oi"]
        gap_str = "-" if oq["oi_gap_max_minutes"] is None else f"{oq['oi_gap_max_minutes']:.1f}"
        md_lines.append(
            f"| {symbol} | {oq['oi_rows_received']} | {gap_str} | "
            f"{oq['oi_first_ts_ms']} | {oq['oi_last_ts_ms']} |"
        )

    md_lines.append("")
    md_lines.append("## Notes")
    md_lines.append("")
    md_lines.append("- Source: documented public archive `data.binance.vision`.")
    md_lines.append("- Live Binance fapi REST is geoblocked from many cloud regions; the CDN is the v1 fallback.")
    md_lines.append("- Status thresholds: green if dedup_ratio>=0.99 and 0 duplicates and 0 out-of-order rows.")

    out_path = repo_root / "data_layer" / "reports" / "quality" / "latest_summary.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md_lines) + "\n")
    return out
