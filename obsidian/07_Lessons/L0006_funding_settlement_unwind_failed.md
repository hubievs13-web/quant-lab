---
id: L0006
slug: funding_settlement_unwind_failed
created: 2026-05-01
related_hypotheses: [H0007]
---

# L0006 - funding_settlement_unwind_failed

## Claim

Scheduled Binance USD-M funding-settlement timing plus bar-only pre-settlement displacement did not produce a valid standalone intraday edge on BTCUSDT and ETHUSDT.

## Evidence

H0007 / S0007 / Determined Orange Mule ran from 2024-01-01 to 2025-01-01. The run produced approximately 509 completed trades, Sharpe -5.112, net profit -48.692 percent, max drawdown 48.900 percent, win rate 32 percent, profit factor 0.73, total fees 48.32 USDT, average pre-fee trade -0.0802 percent, and average post-fee trade -0.1602 percent. Trade count passed, but falsification criteria 2 through 6 failed, so Monte Carlo was not allowed.

## Implication for future hypotheses

Do not treat the funding settlement clock alone as enough futures-specific information. A future funding-related hypothesis needs a genuinely different mechanism and confirmed data availability, such as actual historical funding-rate regimes, basis/premium dislocation, or open-interest state. If those data are unavailable in QuantConnect Lean v17685, the candidate must be marked BLOCKED rather than proxied with bar-only timing.

## Anti-pattern

Changing the settlement window, displacement threshold, hold bars, leverage, sizing, stop-loss, take-profit, cooldown, or adding ordinary price filters is tuning H0007. Rebranding the same scheduled funding-settlement unwind with cosmetic parameter changes is not new research.
