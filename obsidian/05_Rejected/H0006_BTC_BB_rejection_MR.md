---
id: H0006
slug: BTC_BB_rejection_MR
status: rejected
mechanism_class: mean_reversion
symbols: [BTCUSDT]
venue: spot
timeframe: 5m
---

# H0006 — BTC Bollinger Band rejection mean reversion with range filter (BTCUSDT spot, 5m)

## Mechanism (as proposed at the time)

Fade BTCUSDT spot 5m touches of the upper or lower Bollinger band when
a range filter (e.g., ADX below threshold or variance-based regime
classifier) indicated a mean-reverting regime. Exit at the middle band.

## Result

Rejected. Pre-fee edge per trade approximately -0.006 percent.

## Why this is dead

- BB touches on 5m BTC spot are already priced in; the "touch" event
  itself is noisy.
- Range filters that worked in-sample did not generalize out-of-sample.
- Adding the range filter increased parameter count without recovering
  edge.

## Do not repeat

- BTC or ETH spot BB fade with different standard-deviation multipliers
  (tuning).
- Same fade with a different range filter (tuning unless the regime
  classifier itself is a distinct mechanism with independent
  justification).
- Same fade on 3m or 15m spot (tuning the timeframe).
