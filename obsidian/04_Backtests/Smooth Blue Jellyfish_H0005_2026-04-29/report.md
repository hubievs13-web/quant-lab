---
id: Smooth Blue Jellyfish
hypothesis: H0005
strategy: S0005
date: 2026-04-29
symbols: BTCUSDT,ETHUSDT
timeframe: 5m
is_window: [2024-01-01, 2024-01-01]
oos_window: [2024-01-01, 2025-01-01]
evidence_confidence: OK
verdict_draft: READY_FOR_DEVIN_REVIEW
---

# Smooth Blue Jellyfish — H0005 run 2026-04-29

## 1. Metadata

- Hypothesis: `obsidian/02_Hypotheses/H0005_*.md`
- Strategy:   `obsidian/03_Strategies/S0005_*.md`
- Strategy code: `strategies/H0005_*/`
- QC project: 30774195 (Lean v17685)
- Symbols: BTCUSDT,ETHUSDT
- Timeframe: 5m

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

- total_trades: 1696
- net_return: -88.903%
- sharpe: -6.013
- max_drawdown: -36.79
- win_rate: 10%
- profit_factor: 0.1732
- avg_trade_net: 0.12%
- avg_trade_prefee: UNKNOWN

Pre-fee average trade is reconstructed by the user / Devin from
the post-fee average trade plus the assumed round-trip friction
(~0.18 percent) per `obsidian/01_Rules/02_Fee_Slippage_Model.md`.
This script does NOT auto-reconstruct it.

## 4. Falsification Criteria 1-6 (DRAFT, Devin confirms)

| # | Criterion                                 | Observed | Pass |
|---|-------------------------------------------|----------|------|
| 1 | Trade count >= 300 (intraday) or 30 swing | 1696 | UNKNOWN |
| 2 | OOS Sharpe > 1.0                          | -6.013 | UNKNOWN |
| 3 | OOS net avg trade > 0                     | 0.12% | UNKNOWN |
| 4 | Max drawdown < 25 percent                 | -36.79 | UNKNOWN |
| 5 | Pre-fee avg trade >= 0.10 percent         | UNKNOWN  | UNKNOWN |
| 6 | WR >= 50 percent IS+OOS, OR PF >= 1.25    | wr=10%, pf=0.1732 | UNKNOWN |

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
- verdict_draft:       READY_FOR_DEVIN_REVIEW
- reason:              primary artifacts present; criteria 1-6 to be evaluated by Devin

This is a DRAFT only. The Devin chat issues the final verdict.
Possible draft values: FAIL_DRAFT, INCONCLUSIVE_DRAFT,
READY_FOR_DEVIN_REVIEW.

## 8. Notes for Devin

- Primary evidence attached: logs.txt, orders.csv, statistics.json, trades.csv
- Secondary evidence attached: NONE
- Apply Falsification Framework V3 criteria 1-6 to the metrics
  above. If PRELIMINARY_PASS, request Monte Carlo run via
  `scripts/monte_carlo.py` on the trades CSV.

