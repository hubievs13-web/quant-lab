---
id: CE0004
slug: perp_volume_impulse_followthrough
created: 2026-04-29
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
---

# CE0004 - perp_volume_impulse_followthrough

## 1. Mechanism

Large completed perpetual futures volume on a directional 5m bar may indicate aggressive derivatives-side inventory transfer rather than ordinary spot drift. If dealers and leveraged traders continue to rebalance after the initial bar, a small continuation move can occur in the next few bars. The candidate trades the same perpetual in the direction of the completed high-volume impulse.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.07 to 0.12 percent.
- Reasoning from first principles: a strong volume impulse can reflect informed or forced derivatives flow, but same-symbol continuation on short crypto bars is close to the rejected microtrend family. The effect may only barely clear the pre-fee floor in the best regimes and is likely vulnerable to costs.

## 3. Expected trade frequency per day per symbol

- Approximately 5 to 12 trades per day per symbol if volume fields are available and liquid sessions dominate.

## 4. Expected failure modes

- Volume spikes mark exhaustion rather than continuation.
- Same-symbol continuation is too similar to short-horizon noise after costs.
- QC futures bar volume may be missing, inconsistent, or not comparable across contract mappings.
- Entries cluster during volatile periods and produce repeated whipsaws.
- The expected raw move is too small relative to 0.18 percent friction.

## 5. Data required

- Bars: 5m TradeBar data for BTCUSDT and ETHUSDT Binance USD-M Futures.
- Derivatives features: perpetual futures bar volume.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: partial. Price bars are expected; futures bar volume and exact symbol mapping must be verified in QC before implementation.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, or H0006 because it does not rely on spot mean reversion, spread reclaim, wick recovery, or Bollinger rejection. It risks being close to H0004 because it is same-symbol directional follow-through, but its proposed mechanism is derivatives volume imbalance rather than consecutive price bars. Because that distinction may be weak without reliable volume diagnostics, it is not promoted.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 2
- Data availability (1-5): 3
- Simplicity (1-5, higher is simpler): 4
- Total: 12

## 8. Decision

- [ ] Promote to hypothesis. Not selected in this researcher pass because it is too close to same-symbol microtrend unless volume diagnostics prove otherwise.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0004_perp_volume_impulse_followthrough.md`
      with reason. Never delete.
