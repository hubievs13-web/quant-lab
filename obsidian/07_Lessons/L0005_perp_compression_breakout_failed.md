---
id: L0005
slug: perp_compression_breakout_failed
created: 2026-04-29
related_hypotheses: [H0005]
---

# L0005 - perp_compression_breakout_failed

## Claim

Simple same-symbol 5m Binance USD-M futures compression breakout on BTCUSDT/ETHUSDT failed badly after realistic friction.

## Evidence

H0005 / Smooth Blue Jellyfish ran from 2024-01-01 to 2025-01-01. The run ended with start equity 200, end equity 22.19, net profit -88.903%, Sharpe -6.013, drawdown 88.9%, win rate 10%, profit-loss ratio 0.74, expectancy -0.818, total orders 3392, and total fees 79.85. Monte Carlo was not allowed because criteria 1-6 failed.

- Processed backtest report: `../04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/report.md`
- Raw artifacts: `../../results/raw/Smooth_Blue_Jellyfish`

## Implication for future hypotheses

Do not repeat simple same-symbol 5m compression breakout on BTCUSDT/ETHUSDT as the same mechanism with parameter changes. Future futures research needs a genuinely different mechanism, such as funding, OI, basis, or a separately justified regime variable, not just another compression threshold.

## Anti-pattern

Changing compression threshold, `compression_bars`, `hold_bars`, stop-loss, take-profit, cooldown, leverage, or sizing is tuning H0005 and does not create a new hypothesis.
