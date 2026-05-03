"""CLI entrypoint for the Market Research Data Layer.

Phase 1 scaffold: every subcommand prints "not implemented".
Subcommands are wired in subsequent phases per
`DATA_LAYER_IMPLEMENTATION_PLAN.md` Section 12 and gated by user
approval per plan Section 14.

Usage:

    python -m data_layer.scripts.cli --help
"""
from __future__ import annotations

import argparse
import sys

SUBCOMMANDS: dict[str, str] = {
    "fetch": "Fetch raw data from a configured source (Phase 2+).",
    "rebuild": "Rebuild processed/* tables from raw/* (Phase 2+).",
    "refresh-summaries": "Regenerate reports/summaries/* (Phase 6).",
    "query": "Run a named query and emit a small markdown answer (Phase 6).",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data_layer.cli",
        description="Market Research Data Layer CLI (Phase 1 stub).",
    )
    sub = parser.add_subparsers(dest="cmd", metavar="<cmd>")
    for name, desc in SUBCOMMANDS.items():
        sub.add_parser(name, help=desc)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    print(f"data_layer.cli {args.cmd}: not implemented (Phase 1 scaffold)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
