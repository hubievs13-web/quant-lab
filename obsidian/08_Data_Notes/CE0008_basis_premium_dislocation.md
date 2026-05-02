---
id: CE0008
slug: basis_premium_dislocation
created: 2026-04-29
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0008 - basis_premium_dislocation

## 1. Mechanism

Perpetual futures can trade rich or cheap to spot / index when leveraged demand is imbalanced. A large premium that starts compressing can signal crowded longs unwinding; a large discount that starts compressing can signal crowded shorts unwinding. The edge is the basis / premium dislocation and unwind, not a raw price candle pattern.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.25 percent if reliable premium or basis data is available.
- Reasoning from first principles: basis reflects the difference between perpetual pricing and reference value, a futures-specific pressure variable. Compression after an extreme can create directional pressure large enough to clear 0.10 percent pre-fee, but only if the premium/index data is real and timestamp-aligned.

## 3. Expected trade frequency per day per symbol

- Approximately 1 to 5 trades per day per symbol, depending on premium extremes.

## 4. Expected failure modes

- Basis stays extreme during persistent trends and compression does not occur.
- Premium/index data is unavailable or not timestamp-aligned in QC.
- The signal is too sparse to reach 300 OOS trades.
- Basis compression is already reflected in futures price before execution.
- Spot/index proxy substitution introduces data leakage or a non-native data dependency.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: premium index, mark/index price, or reliable basis series.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no / not confirmed by local data notes. Treat as blocked unless QC-native premium/index/basis history is verified.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0006, or H0002. It does not use spot spread reclaim, wick geometry, same-symbol microtrend, Bollinger rejection, or BTC-to-ETH lead-lag. The mechanism is a perpetual basis / premium dislocation, which is futures-specific and data-dependent.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 2
- Total: 11

## 8. Decision

- [ ] Promote to hypothesis. Not selected because required basis / premium data is not confirmed in QC Lean v17685.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0008_basis_premium_dislocation.md`
      with reason. Never delete.
