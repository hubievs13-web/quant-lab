# 04_Monte_Carlo_Protocol

Used only after a hypothesis has cleared criteria 1 to 6 (PRELIMINARY
PASS). The Devin chat owns the FINAL_PASS / FAIL decision; the script
output is evidence, not a verdict.

## Inputs

- Trade-by-trade post-fee PnL list as a CSV with one of these supported
  columns:
  - `pnl_pct` (preferred)
  - `return_pct`
  - `pnl_percent`
  - `profit_pct`
  - `net_return_pct`
- Starting capital: USD 200 by default. The capital used for MC must
  match the assumption used in the QuantConnect backtest. Document
  any deviation in the backtest report.
- Trade count N: use all OOS trades.

## Modes

- `bootstrap` (default): draw N trades with replacement from the pool.
  Tests robustness of both final equity and drawdown to sampling noise.
  Used for the framework V3 pass condition.
- `shuffle`: reorder the same set of trades. Tests drawdown ordering
  only. NOTE: with purely multiplicative percent returns and fixed
  fractional sizing, final equity is order-invariant (commutative).
  Shuffle still varies the path so min-equity / max-drawdown changes.

## Pass conditions (all must hold)

A Monte Carlo PASS requires:

1. P5 of final equity > starting capital.
2. P95 of max drawdown < 25 percent.
   (For drawdown smaller is better, so the worse-tail is the high
   percentile. P95 is the drawdown such that 95 percent of simulated
   paths had a smaller-or-equal drawdown.)
3. Probability(final equity < starting capital) < 5 percent.
4. Trade count N >= the minimum used in framework criterion 1
   (intraday: 300; swing: 30). Below threshold => INCONCLUSIVE,
   never PASS.

If any condition fails => MC FAIL.
If condition 4 fails alone => INCONCLUSIVE.

## Output format from `scripts/monte_carlo.py`

The script prints (and may also write to a file):

- mode
- column_used
- trades                   (observed trade count)
- simulations
- start_equity
- median_final_equity
- p5_final_equity
- p95_final_equity
- median_max_drawdown_pct
- p95_max_drawdown_pct
- prob_final_below_start
- min_trades_threshold
- verdict_draft            (PASS / FAIL / INCONCLUSIVE)

Exit codes:

- 0  PASS
- 1  FAIL
- 2  INPUT_ERROR (e.g. unsupported CSV column, unreadable file)
- 3  INCONCLUSIVE

The `verdict_draft` line is a draft only. The Devin chat issues the
final verdict.

## Caveats

- Bootstrap with replacement assumes independent trades. If trades are
  clearly serially correlated (e.g., overlapping positions), treat the
  P5 numbers as a lower-bound noise check, not sufficiency.
- The script does not model funding payments, partial fills, or
  exchange outages. Those are accounted for upstream in the QC backtest
  and via the slippage buffer in the fee model.

## Implementation

`scripts/monte_carlo.py`. Run with:

```
python scripts/monte_carlo.py results/trades/<file>.csv \
    --mode bootstrap --sims 1000 --start 200
```

Pipe the output into `obsidian/04_Backtests/BTxxxx_.../report.md` as
the Monte Carlo section before sending the report to the Devin chat.
