---
id: H0003
slug: SOL_liquidation_wick
status: rejected
mechanism_class: mean_reversion
symbols: [SOLUSD]
venue: spot
timeframe: 5m
---

# H0003 — SOL liquidation wick recovery (SOLUSD spot, 5m)

## Mechanism (as proposed at the time)

Long wicks on 5m candles were hypothesized to reflect liquidation
cascades on derivatives venues spilling into spot. Enter mean reversion
after a wick that exceeded N ATRs and exited once the candle body
closed near the prior level.

## Result

Rejected. Pre-fee edge per trade approximately -0.05 percent.

## Why this is dead

- On spot, without access to real liquidation feeds, the wick signal is
  ambiguous. Many wicks are not liquidation driven.
- When a true liquidation cascade occurs, the reversion is either too
  fast to fill at a good price or does not come (continuation).
- Historical liquidation data is not reliably available for free.
  Proxying via wick geometry alone is not enough.

## Do not repeat

- SOL wick revert at different ATR multipliers (tuning).
- SOL wick revert with confirmation candle (same mechanism with extra
  filter; counts as tuning unless the filter is its own mechanism).
- BTC or ETH spot wick revert in the same spirit without a distinct
  mechanism.
