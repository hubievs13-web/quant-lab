---
id: H0004
slug: BTC_microtrend_trailing
status: rejected
mechanism_class: momentum
symbols: [BTCUSDT]
venue: spot
timeframe: 1m
---

# H0004 — BTC microtrend trailing (BTCUSDT spot, 1m)

## Mechanism (as proposed at the time)

Short-horizon momentum on BTCUSDT spot at 1m: after N consecutive bars
in one direction, enter in the direction of the microtrend and trail
with a percentage stop. Expected edge from intraday momentum
persistence.

## Result

Rejected. Pre-fee edge per trade approximately -0.01 percent.

## Why this is dead

- 1m BTC spot microtrends are dominated by noise. Signal ACF is close
  to zero at the lags tested.
- Trailing stops round-trip out of positions at unfavorable prices
  during fast chop.
- Post-fee edge well below zero; pre-fee edge also below zero.

## Do not repeat

- BTC 1m microtrend with different N-of-M bar rules (tuning).
- BTC 1m microtrend with different trailing-stop percentages (tuning).
- BTC/ETH spot microtrend on 3m or 5m as "new" timeframes (tuning the
  timeframe is still tuning unless the mechanism changes).
