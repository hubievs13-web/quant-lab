---
id: H0001
slug: ETH_spread_reclaim
status: rejected
mechanism_class: mean_reversion
symbols: [ETHUSDC]
venue: spot
timeframe: 1m
---

# H0001 — ETH spread reclaim mean reversion (ETHUSDC spot, 1m)

## Mechanism (as proposed at the time)

After a sharp dislocation in the bid-ask spread on ETHUSDC, price was
expected to mean-revert to the prior mid within a few minutes. Entry on
a widened spread print followed by a reclaim of the prior mid.

## Result

Rejected. Pre-fee edge per trade approximately 0 percent. After fees,
clearly unprofitable.

## Why this is dead

- Spot venues with tight liquidity do not leave tradable mean-reversion
  after fees at 1m on ETHUSDC.
- The "reclaim" signal lagged execution; by the time the condition
  fired, mid had already normalized.

## Do not repeat

Do NOT file any of these as "new" hypotheses:

- ETH or BTC spread reclaim on spot (same mechanism).
- Same setup with a different moving-average window (tuning).
- Same setup with a different cooldown (tuning).

A new hypothesis requires a different mechanism, not a different window.
