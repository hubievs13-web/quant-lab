---
id: BT0001
hypothesis: H0002
strategy: S0001
date: 2026-04-29
symbols: UNKNOWN
timeframe: UNKNOWN
is_window: [UNKNOWN, UNKNOWN]
oos_window: [UNKNOWN, UNKNOWN]
evidence_confidence: OK
verdict_draft: INCONCLUSIVE_DRAFT
---

# BT0001 — H0002 run 2026-04-29

## 1. Metadata

- Hypothesis: `obsidian/02_Hypotheses/H0002_*.md`
- Strategy:   `obsidian/03_Strategies/S0001_*.md`
- Strategy code: `strategies/H0002_*/`
- QC project: 30774195 (Lean v17685)
- Symbols: UNKNOWN
- Timeframe: UNKNOWN

## 2. Files

- logs.txt (primary)
- orders.csv (primary)
- statistics.json (primary)
- trades.csv (primary)

Missing well-known files:

- MISSING: equity_curve.png
- MISSING: overview.png
- MISSING: report.pdf
- MISSING: statistics.txt

Evidence policy: machine-readable files (trades.csv, orders.csv,
logs.txt, statistics.*) are PRIMARY. Screenshots and report.pdf
are SECONDARY. If only secondary evidence is present, this report
is marked LOW_CONFIDENCE.

## 3. Key Metrics (extracted from artifacts; UNKNOWN if not found)

- total_trades: 132
- net_return: -14.608%
- sharpe: -0.774
- max_drawdown: -16.69
- win_rate: 31%
- profit_factor: 1.6995
- avg_trade_net: 1.82%
- avg_trade_prefee: UNKNOWN

Pre-fee average trade is reconstructed by the user / Devin from
the post-fee average trade plus the assumed round-trip friction
(~0.18 percent) per `obsidian/01_Rules/02_Fee_Slippage_Model.md`.
This script does NOT auto-reconstruct it.

## 4. Falsification Criteria 1-6 (DRAFT, Devin confirms)

| # | Criterion                                 | Observed | Pass |
|---|-------------------------------------------|----------|------|
| 1 | Trade count >= 300 (intraday) or 30 swing | 132 | UNKNOWN |
| 2 | OOS Sharpe > 1.0                          | -0.774 | UNKNOWN |
| 3 | OOS net avg trade > 0                     | 1.82% | UNKNOWN |
| 4 | Max drawdown < 25 percent                 | -16.69 | UNKNOWN |
| 5 | Pre-fee avg trade >= 0.10 percent         | UNKNOWN  | UNKNOWN |
| 6 | WR >= 50 percent IS+OOS, OR PF >= 1.25    | wr=31%, pf=1.6995 | UNKNOWN |

## 5. Missing Data

- equity_curve.png: not provided in raw dir.
- overview.png: not provided in raw dir.
- report.pdf: not provided in raw dir.
- statistics.txt: not provided in raw dir.

## 6. Diagnostics

Items to verify in logs.txt before sending to Devin:

- signal-bar vs execution-bar timestamps (no leakage).
- brokerage-model warnings (Binance Futures support).
- data-gap or stale-quote warnings.
- daily summaries emitted by the strategy.

## 7. Preliminary Verdict Draft

- evidence_confidence: OK
- verdict_draft:       INCONCLUSIVE_DRAFT
- reason:              trade count 132 below intraday minimum 300

This is a DRAFT only. The Devin chat issues the final verdict.
Possible draft values: FAIL_DRAFT, INCONCLUSIVE_DRAFT,
READY_FOR_DEVIN_REVIEW.

## 8. Notes for Devin

- Primary evidence attached: logs.txt, orders.csv, statistics.json, trades.csv
- Secondary evidence attached: NONE
- Apply Falsification Framework V3 criteria 1-6 to the metrics
  above. If PRELIMINARY_PASS, request Monte Carlo run via
  `scripts/monte_carlo.py` on the trades CSV.


## 9. Devin Final Verdict Addendum

- Date recorded: 2026-04-29.
- External Devin verdict: FAIL / REJECTED.
- This supersedes the earlier script-generated draft fields in this report.
- Monte Carlo: NOT RUN because Falsification Framework V3 criteria 1-6 failed.

### Final metrics used for rejection

- Start Equity: 200 USDT.
- End Equity: 170.78 USDT.
- Net Profit: -14.608%.
- Sharpe: -0.774.
- Drawdown: 28.3%.
- Win Rate: 31%.
- Loss Rate: 69%.
- Total Orders: 278.
- Approx completed trades: 132.
- Total Fees: 43.07 USDT.
- Profit-Loss Ratio: 1.90.
- Expectancy: -0.098.

### Failed criteria

- Trade count >= 300: FAIL, only 132 completed trades.
- OOS Sharpe > 1.0: FAIL, Sharpe -0.774.
- OOS net average trade > 0: FAIL, expectancy -0.098.
- Max drawdown < 25 percent: FAIL, drawdown 28.3%.
- Pre-fee average >= 0.10 percent per trade: not proven / failed to establish from result.
- WR >= 50 percent or PF >= 1.25 with stable payoff ratio: FAIL, WR 31%; PF alone is not enough because net result and Sharpe failed.

### Recording actions

- H0002 moved to `obsidian/05_Rejected/H0002_btc_perp_eth_lag.md`.
- Post-mortem appended to rejected hypothesis note.
- Lesson recorded at `obsidian/07_Lessons/L0002_simple_btc_eth_perp_lead_lag_failed.md`.
- `experiments_log.md` and `results/experiments.csv` updated with the final Devin verdict.
