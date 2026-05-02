---
id: L0001
slug: spot_below_5m_no_edge
created: 2026-04-29
related_hypotheses: [H0001, H0003, H0004, H0006]
---

# L0001 — BTC/ETH/SOL spot <=5m mean-reversion and microtrend did not survive costs

## Claim

Plain-vanilla mean-reversion and microtrend patterns on BTC/ETH/SOL
spot at timeframes <= 5m do not produce a tradable edge after realistic
fees and slippage. Pre-fee edge per trade was approximately 0 or
negative across four independent hypotheses (H0001, H0003, H0004,
H0006).

## Evidence

- H0001 (ETH spread reclaim, 1m spot): pre-fee ~0 percent.
- H0003 (SOL liquidation wick, 5m spot): pre-fee ~-0.05 percent.
- H0004 (BTC microtrend trailing, 1m spot): pre-fee ~-0.01 percent.
- H0006 (BTC BB fade with range filter, 5m spot): pre-fee ~-0.006
  percent.

## Implication for future hypotheses

- New v1 hypotheses must be on Binance USD-M Futures, not spot.
- New v1 hypotheses must use a mechanism that is futures-specific and
  not present on spot (funding, open interest, basis / perp-spot
  divergence, derivatives-side order flow, lead-lag from perpetual
  liquidity).
- A generic "mean reversion on BTC 5m" or "momentum on BTC 1m" with new
  indicators is presumed to fail absent a new mechanism. It is not
  enough to add an indicator; the mechanism must be structurally
  different.

## Anti-pattern

- Adding ATR, EMA, RSI or ADX filters to a rejected mean-reversion
  setup. This is tuning disguised as a new idea.
- Changing timeframe from 1m to 3m or 5m. Same.
- Changing symbol among BTC/ETH/SOL spot while keeping the same
  mechanism. Same.
