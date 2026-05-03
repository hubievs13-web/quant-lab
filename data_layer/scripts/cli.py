"""CLI entrypoint for the Market Research Data Layer.

Phase 2 wired the ingest + quality smoke commands; Phase 3 adds
features + regimes. Future-phase subcommands still stub-print.

Usage:

    python -m data_layer.scripts.cli --help
    python -m data_layer.scripts.cli fetch-binance-smoke
    python -m data_layer.scripts.cli rebuild-smoke
    python -m data_layer.scripts.cli quality-smoke
    python -m data_layer.scripts.cli build-features-smoke
    python -m data_layer.scripts.cli build-regimes-smoke
    python -m data_layer.scripts.cli detect-events-smoke
    python -m data_layer.scripts.cli build-outcomes-smoke
    python -m data_layer.scripts.cli build-leaderboard-smoke
    python -m data_layer.scripts.cli refresh-summaries
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SUBCOMMANDS: dict[str, str] = {
    "fetch-binance-smoke": "Phase 2 smoke: fetch BTCUSDT OHLCV+funding+OI from data.binance.vision.",
    "rebuild-smoke": "Phase 2 smoke: align + join local raw/ into processed/.",
    "quality-smoke": "Phase 2 smoke: emit quality JSONs + reports/quality/latest_summary.md.",
    "build-features-smoke": "Phase 3 smoke: compute features for BTCUSDT 5m/1h.",
    "build-regimes-smoke": "Phase 3 smoke: compute regime labels for BTCUSDT 5m/1h.",
    "detect-events-smoke": "Phase 4 smoke: detect events for BTCUSDT 5m/1h.",
    "build-outcomes-smoke": "Phase 4 smoke: build forward outcomes for BTCUSDT 5m/1h.",
    "build-leaderboard-smoke": "Phase 4 smoke: aggregate leaderboard for BTCUSDT 5m/1h.",
    "refresh-summaries": "Regenerate reports/summaries/* and reports/leaderboards/*.",
    "fetch": "Generic fetch (Phase 5+).",
    "rebuild": "Generic rebuild (Phase 5+).",
    "query": "Run a named query (Phase 6).",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data_layer.cli",
        description="Market Research Data Layer CLI (Phase 2).",
    )
    sub = parser.add_subparsers(dest="cmd", metavar="<cmd>")
    for name, desc in SUBCOMMANDS.items():
        sub.add_parser(name, help=desc)
    return parser


def _run_quality_smoke() -> int:
    from data_layer.process.quality import run_quality_smoke

    repo_root = Path(__file__).resolve().parents[2]
    store_root = repo_root / "data_layer" / "store"
    out = run_quality_smoke(
        repo_root=repo_root,
        store_root=store_root,
        symbols=["BTCUSDT"],
        series=[("5m", 7), ("1h", 30)],
        funding_window_days=30,
        oi_window_days=7,
    )
    print(f"[quality] wrote data_layer/reports/quality/latest_summary.md")
    print(f"[quality] series:")
    for sym, sym_out in out.items():
        for tf, q in sym_out.get("ohlcv", {}).items():
            print(
                f"  {sym} {tf}: status={q['status']} "
                f"received={q['received_bars']}/{q['expected_bars']} "
                f"dups={q['duplicate_bars']} ooo={q['out_of_order_rows']}"
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    if args.cmd == "fetch-binance-smoke":
        from data_layer.scripts.fetch import fetch_binance_smoke

        return fetch_binance_smoke()
    if args.cmd == "rebuild-smoke":
        from data_layer.scripts.rebuild import rebuild_smoke

        return rebuild_smoke()
    if args.cmd == "quality-smoke":
        return _run_quality_smoke()
    if args.cmd == "build-features-smoke":
        from data_layer.process.features import build_features_smoke

        return build_features_smoke()
    if args.cmd == "build-regimes-smoke":
        from data_layer.process.regimes import build_regimes_smoke

        return build_regimes_smoke()
    if args.cmd == "detect-events-smoke":
        from data_layer.process.events import detect_events_smoke

        return detect_events_smoke()
    if args.cmd == "build-outcomes-smoke":
        from data_layer.process.outcomes import build_outcomes_smoke

        return build_outcomes_smoke()
    if args.cmd == "build-leaderboard-smoke":
        from data_layer.process.leaderboard import build_leaderboard_smoke

        return build_leaderboard_smoke()
    if args.cmd == "refresh-summaries":
        from data_layer.scripts.refresh_summaries import refresh_all_summaries

        return refresh_all_summaries()
    print(f"data_layer.cli {args.cmd}: not implemented (later phase)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
