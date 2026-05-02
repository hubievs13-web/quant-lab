---
id: CE0010
slug: higher_tf_perp_regime_pullback
created: 2026-04-29
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
---

# CE0010 - higher_tf_perp_regime_pullback

## 1. Mechanism

Perpetual futures can spend several hours in a leverage-driven directional regime after a large liquidation-free repricing wave. A shallow pullback inside that regime may continue as futures traders re-enter in the regime direction. The idea is a higher-timeframe futures regime with intraday pullback entries, not a 1m or 5m microtrend count.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.10 to 0.16 percent.
- Reasoning from first principles: higher-timeframe regime continuation can create larger raw moves than isolated 5m momentum. However, without OI/funding confirmation, the mechanism risks becoming generic trend following, so the edge floor is only barely justified.

## 3. Expected trade frequency per day per symbol

- Approximately 1 to 4 trades per day per symbol.
- Across BTCUSDT and ETHUSDT combined, approximately 2 to 8 trades per day.

## 4. Expected failure modes

- The higher-timeframe regime label is just price momentum and duplicates rejected microtrend behavior.
- Pullbacks deepen into reversals instead of continuation.
- Trade count may fall below 300 OOS if regime filters are strict.
- Without funding/OI, the strategy cannot distinguish leveraged futures regime from ordinary price drift.
- Friction consumes the small pullback continuation edge.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: none if implemented bar-only; funding/OI would improve mechanism but is not assumed.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: yes / expected for price bars, with verification required. Exact project symbol mapping must be verified before implementation.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0006, or H0002 because it is not spot mean reversion, wick recovery, Bollinger rejection, or BTC-to-ETH lead-lag. It risks being too close to H0004 if reduced to same-symbol short-horizon momentum, so it is parked rather than promoted unless a stronger independent futures-regime definition is created.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 2
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 3
- Total: 12

## 8. Decision

- [ ] Promote to hypothesis. Not selected because it risks becoming a disguised same-symbol momentum variant without independent futures-regime data.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0010_higher_tf_perp_regime_pullback.md`
      with reason. Never delete.
