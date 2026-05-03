"""Regenerate small Codex-readable markdown summaries (Phase 2 subset).

Phase 2 emits only `data_layer/reports/summaries/universe_status.md`.
Future phases will add `regime_summary.md`, `event_catalog.md`, etc.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
REPORTS = REPO_ROOT / "data_layer" / "reports"
SYMBOL = "BTCUSDT"


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


def refresh_universe_status() -> int:
    lines: list[str] = []
    lines.append("# Universe Status")
    lines.append("")
    lines.append(f"Last refresh: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M UTC')}.")
    lines.append("")
    lines.append("## Loaded series (binance, BTCUSDT)")
    lines.append("")
    lines.append("| timeframe | first bar | last bar | rows |")
    lines.append("|---|---|---|---|")
    for tf in ("5m", "1h"):
        n, first, last = _read_meta(
            STORE_ROOT / "processed/bars/binance" / SYMBOL / f"{tf}.parquet"
        )
        lines.append(f"| {tf} | {_ms_to_str(first)} | {_ms_to_str(last)} | {n} |")

    lines.append("")
    lines.append("## Derivatives")
    lines.append("")
    lines.append("- Funding rate: see `data_layer/reports/quality/latest_summary.md`.")
    lines.append("- Open Interest (5-min metrics): see `data_layer/reports/quality/latest_summary.md`.")
    lines.append("")
    lines.append("## Pending phases")
    lines.append("")
    lines.append("- Phase 3 (features + regimes): pending approval")
    lines.append("- Phase 4 (events + outcomes + leaderboard): pending approval")
    lines.append("- Phase 5 (Bybit + OKX): pending approval")
    lines.append("- Phase 6 (hypothesis seed briefs): pending approval")
    lines.append("- Phase 7 (liquidations + book): deferred")
    lines.append("")
    lines.append("Read order for Codex / Devin: see `data_layer/README.md`.")

    out = REPORTS / "summaries" / "universe_status.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"[summaries] wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(refresh_universe_status())
