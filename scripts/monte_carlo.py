"""Monte Carlo audit on per-trade PnL.

Pass conditions (Falsification Framework V3, full set):

1. P5(final equity) > starting capital.
2. P95(max drawdown) < 25 percent.
   (Worse-tail: high percentile is bad for drawdown, since smaller is
   better. P95 is the 95th worst path's drawdown.)
3. P(final equity < starting capital) < 5 percent.
4. trade_count >= min_trades_threshold (default 300 intraday).
   Below threshold => verdict_draft = INCONCLUSIVE, not PASS.

Final verdict is owned by the Devin chat. This script outputs a
verdict_draft only.

Exit codes:
    0  PASS
    1  FAIL
    2  INPUT_ERROR (e.g., bad CSV column, unreadable file)
    3  INCONCLUSIVE

Two modes:

- bootstrap (default): draw N trades with replacement. Tests robustness
  of final equity and drawdown.
- shuffle: reorder the same set of trades. Drawdown varies. With
  purely multiplicative percent returns and fixed fractional sizing,
  final equity is order-invariant (commutative); shuffle still varies
  the equity path so min-equity / max-drawdown changes.

Input CSV: any of the following column names is accepted (first match
wins):
    pnl_pct (preferred)
    return_pct
    pnl_percent
    profit_pct
    net_return_pct

Per-trade returns must be in PERCENT and post-fee (e.g. 0.25 = +0.25
percent on equity). The script does not invent a return column from
unrelated fields.

Usage:
    python scripts/monte_carlo.py trades.csv \\
        --mode bootstrap --sims 1000 --start 200 [--min-trades 300]
"""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import sys
from pathlib import Path

SUPPORTED_COLUMNS = (
    "pnl_pct",
    "return_pct",
    "pnl_percent",
    "profit_pct",
    "net_return_pct",
)


def load_trade_returns(path: Path) -> tuple[list[float], str]:
    with path.open() as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        chosen: str | None = None
        for name in SUPPORTED_COLUMNS:
            if name in fields:
                chosen = name
                break
        if chosen is None:
            # Exit 2: INPUT_ERROR.
            print("ERROR: No supported return column found in CSV.", file=sys.stderr)
            print(f"  file:    {path}", file=sys.stderr)
            print(f"  columns: {fields}", file=sys.stderr)
            print(
                f"  expected one of: {', '.join(SUPPORTED_COLUMNS)}",
                file=sys.stderr,
            )
            print(
                "  the column must contain per-trade return in PERCENT, "
                "post-fee (e.g. 0.25 means +0.25 percent).",
                file=sys.stderr,
            )
            print(
                "  do not invent the column. add it upstream from your QC "
                "trades export, or rename an existing post-fee return "
                "column to one of the supported names.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        returns: list[float] = []
        for row in reader:
            raw = (row.get(chosen) or "").strip()
            if raw == "":
                continue
            returns.append(float(raw))
    if not returns:
        raise SystemExit(f"{path}: no trades found in column '{chosen}'")
    return returns, chosen


def simulate_path(order: list[float], start: float) -> tuple[float, float]:
    """Return (final_equity, max_drawdown_pct)."""
    equity = start
    peak = start
    max_dd = 0.0
    for r in order:
        equity *= 1.0 + r / 100.0
        if equity <= 0.0:
            return 0.0, 100.0
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0
        if dd > max_dd:
            max_dd = dd
    return equity, max_dd


def simulate(
    returns: list[float],
    start: float,
    sims: int,
    seed: int,
    mode: str,
) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    finals: list[float] = []
    dds: list[float] = []
    n = len(returns)
    for _ in range(sims):
        if mode == "shuffle":
            order = list(returns)
            rng.shuffle(order)
        elif mode == "bootstrap":
            order = [returns[rng.randrange(n)] for _ in range(n)]
        else:
            raise SystemExit(f"unknown mode: {mode}")
        fe, dd = simulate_path(order, start)
        finals.append(fe)
        dds.append(dd)
    return finals, dds


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] + (s[hi] - s[lo]) * frac


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Monte Carlo audit (Falsification Framework V3 draft verdict)"
    )
    parser.add_argument("trades_csv", type=Path)
    parser.add_argument("--start", type=float, default=200.0, help="starting capital (USD)")
    parser.add_argument("--sims", type=int, default=1000, help="number of simulations")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--mode",
        choices=("bootstrap", "shuffle"),
        default="bootstrap",
        help="bootstrap (default): sample with replacement; shuffle: reorder only",
    )
    parser.add_argument(
        "--min-trades",
        type=int,
        default=300,
        help="minimum trade count for a PASS draft; below => INCONCLUSIVE",
    )
    parser.add_argument(
        "--max-dd-pct",
        type=float,
        default=25.0,
        help="max acceptable P95 max drawdown in percent (default 25)",
    )
    parser.add_argument(
        "--max-prob-loss",
        type=float,
        default=5.0,
        help="max acceptable P(final < start) in percent (default 5)",
    )
    args = parser.parse_args(argv)

    returns, column_used = load_trade_returns(args.trades_csv)
    finals, dds = simulate(returns, args.start, args.sims, args.seed, args.mode)

    fe_p5 = percentile(finals, 5.0)
    fe_p50 = statistics.median(finals)
    fe_p95 = percentile(finals, 95.0)
    dd_p95 = percentile(dds, 95.0)
    dd_p50 = statistics.median(dds)
    losers = sum(1 for x in finals if x < args.start)
    prob_loss = losers / len(finals) * 100.0 if finals else float("nan")

    cond_eq = fe_p5 > args.start
    cond_dd = dd_p95 < args.max_dd_pct
    cond_pl = prob_loss < args.max_prob_loss
    cond_n = len(returns) >= args.min_trades

    if not cond_n:
        verdict = "INCONCLUSIVE"
    elif cond_eq and cond_dd and cond_pl:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    print(f"mode                    : {args.mode}")
    print(f"column_used             : {column_used}")
    print(f"trades                  : {len(returns)}")
    print(f"min_trades_threshold    : {args.min_trades}")
    print(f"simulations             : {args.sims}")
    print(f"start_equity            : {args.start:.2f}")
    print(f"median_final_equity     : {fe_p50:.2f}")
    print(f"p5_final_equity         : {fe_p5:.2f}")
    print(f"p95_final_equity        : {fe_p95:.2f}")
    print(f"median_max_drawdown_pct : {dd_p50:.2f}")
    print(f"p95_max_drawdown_pct    : {dd_p95:.2f}")
    print(f"prob_final_below_start  : {prob_loss:.2f} %")
    print(f"cond_final_p5_gt_start  : {cond_eq}")
    print(f"cond_dd_p95_lt_max      : {cond_dd}")
    print(f"cond_prob_loss_lt_max   : {cond_pl}")
    print(f"cond_trade_count_ok     : {cond_n}")
    print(f"verdict_draft           : {verdict}")
    if verdict == "PASS":
        return 0
    if verdict == "INCONCLUSIVE":
        return 3
    return 1  # FAIL


if __name__ == "__main__":
    sys.exit(main())
