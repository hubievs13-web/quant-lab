---
id: CE0022
slug: mark_last_dislocation_snapback
created: 2026-05-02
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0022 - mark_last_dislocation_snapback

## 1. Mechanism

Binance mark price is used for liquidation and margin mechanics, while last trade price reflects executable perp prints. A sharp gap between last price and mark price can indicate temporary aggressive flow or trigger pressure that may snap back when last price overextends relative to the mark/index reference. The edge would come from mark-price mechanics specific to perpetuals, not from a candle pattern alone.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.10 to 0.15 percent, but with high uncertainty.
- Reasoning from first principles: trigger-related dislocations can be abrupt and may exceed normal 5m noise, especially around fast liquidation-risk conditions. The edge floor is plausible only for extreme mark-last dislocations; ordinary small spreads are likely too small after friction.

## 3. Expected trade frequency per day per symbol

- Expected combined BTCUSDT and ETHUSDT frequency: 4 to 10 trades per day if extreme dislocations are not too rare.
- Per symbol: roughly 2 to 5 trades per day.

## 4. Expected failure modes

1. Mark-last spread is usually too small to overcome fees and slippage.
2. Dislocation reflects informed flow and continues instead of snapping back.
3. The correction occurs inside the signal bar, before next-bar execution is possible.
4. Mark price updates smoothly, so the signal is delayed and not causal enough.
5. Extreme dislocations cluster during crashes, increasing correlated downside.

## 5. Data required

- Bars: audited `um_klines_1m`.
- Derivatives features: audited `mark_price_klines` and `index_price_klines`; optional `premium_index_klines`.
- Availability: available in local audited TIER 1 data with DL0007 no-fill/no-signal exception.
- DL0007 handling: missing price-state rows and dependent complete-source 5m bars are no-signal.
- QuantConnect native availability: not assumed; later QC use would require separate approval.

## 6. Distinct-from-rejected statement

This is not H0001/H0006 mean reversion because the reversal object is the mark-last dislocation, a perpetual margin/trigger variable, not a generic price band. It is not H0003 liquidation wick recovery because it does not infer liquidations from wick geometry or require liquidation feeds. It is not H0004 microtrend or H0005 compression breakout because it is not ordinary OHLCV continuation. It is not H0007 because it does not use the funding clock.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 5
- Simplicity (1-5, higher is simpler): 4
- Risk of disguised rejected mechanism (1-5, higher is lower risk): 3
- Total: 19

## 8. Decision

- [ ] Promote to hypothesis as `Hxxxx_<slug>.md`.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0022_mark_last_dislocation_snapback.md` with reason.
