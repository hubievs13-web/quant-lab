---
id: CE0015
slug: liquidation_cascade_aftershock
created: 2026-05-01
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
---

# CE0015 - liquidation_cascade_aftershock

## 1. Mechanism

Large forced liquidation waves in perpetual futures can create aftershock flow as bankrupt positions are cleared, hedges are adjusted, and residual leverage is reduced. A real liquidation-feed signal could support either short continuation during the cascade or reversal after the forced flow exhausts. The edge would be futures-specific only if it uses actual liquidation records, not candle wicks.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.15 to 0.35 percent if reliable historical liquidation data is available.
- Reasoning from first principles: liquidation cascades are forced-flow events and can move BTCUSDT or ETHUSDT more than the 0.10 percent floor over short horizons. However, the repository explicitly marks free reliable historical liquidation data as unavailable, so this cannot be promoted in v1.

## 3. Expected trade frequency per day per symbol

- Approximately 0 to 4 trades per day per symbol, depending on liquidation intensity thresholds and market regime.

## 4. Expected failure modes

- Historical liquidation data is unavailable or paywalled.
- Wick geometry is used as a proxy and repeats the failed H0003 mistake.
- True liquidation waves either revert too fast for next-bar execution or continue violently against a reversal entry.
- Large liquidation periods are highly clustered and can create correlated losses.
- Trade count may be too low in quiet markets.

## 5. Data required

- Bars: 1m or 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: reliable historical liquidation events with side, size, symbol, and timestamp.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no. Local data notes mark historical liquidations as UNAVAILABLE and forbid reconstructing them from price wicks.
- If unavailable: this candidate is BLOCKED until an alternative is approved in writing by the user. Do NOT proxy with wick geometry or unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0004, H0005, H0006, or H0002 because it is not spot spread reclaim, microtrend, compression breakout, Bollinger rejection, or BTC-to-ETH lead-lag. It is close to H0003 in topic, but the note explicitly rejects wick-based liquidation inference; without actual liquidation data, it is blocked rather than converted into a disguised H0003 variant.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 1
- Total: 10

## 8. Decision

- [ ] Promote to hypothesis. BLOCKED because free reliable historical liquidation data is unavailable in v1.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0015_liquidation_cascade_aftershock.md`
      with reason. Never delete.
