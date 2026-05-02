# 01_Falsification_Framework_V3

Single source of truth for verdicts. Mirrors AGENTS.md section 6.

## Required criteria

A hypothesis FAILS if any required criterion fails.

1. Trade count
   - Intraday / high frequency: >= 300 trades.
   - Swing: >= 30 trades.
   - Below threshold: INCONCLUSIVE or FAIL depending on context.
2. OOS Sharpe > 1.0.
3. OOS net average trade > 0.
4. Max drawdown < 25 percent.
5. Pre-fee average trade >= 0.10 percent per trade.
6. Either
   - Win rate >= 50 percent in both IS and OOS, OR
   - Profit factor >= 1.25 with stable payoff ratio.
7. Monte Carlo audit (full pass conditions, see
   `04_Monte_Carlo_Protocol.md`)
   - At least 1000 simulations on per-trade post-fee returns.
   - Trade count must meet the minimum used in criterion 1; otherwise
     MC verdict = INCONCLUSIVE, not PASS.
   - P5 of final equity must be strictly greater than starting capital.
   - P95 of max drawdown must be less than 25 percent.
     (Drawdown: smaller is better, so the worse-tail is the high
     percentile. P95 = path such that 95 percent of sims had drawdown
     no greater.)
   - Probability(final equity < starting capital) must be less than 5
     percent.
   - All four conditions must hold for MC PASS.

## Verdict order

- Step A: analyze criteria 1 to 6.
- Step B:
  - If any of 1 to 6 fails: FAIL.
  - If evidence insufficient: INCONCLUSIVE.
  - Else: PRELIMINARY PASS.
- Step C: only after PRELIMINARY PASS, run Monte Carlo.
- Step D:
  - MC passes: FINAL PASS.
  - MC fails: FAIL.

## What falsification forbids

- Tuning parameters after a failed backtest.
- Promoting a hypothesis from PRELIMINARY PASS to FINAL PASS without
  MC.
- Inventing extra criteria to rescue a borderline result.
- Moving the goalposts between runs.
