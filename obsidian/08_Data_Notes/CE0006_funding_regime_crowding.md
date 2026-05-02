---
id: CE0006
slug: funding_regime_crowding
created: 2026-04-29
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
---

# CE0006 - funding_regime_crowding

## 1. Mechanism

Persistent positive funding can indicate crowded long perpetual positioning; persistent negative funding can indicate crowded short perpetual positioning. A futures-specific edge may exist when price starts moving against the funding crowd after funding has stayed extreme, because leveraged positions can de-risk and amplify the reversal. This is structurally a funding-crowding regime hypothesis, not a price-only mean-reversion signal.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.15 to 0.30 percent if historical funding data is available and aligned without leakage.
- Reasoning from first principles: funding is a direct transfer between long and short perpetual holders and can identify crowding pressure that spot candles do not contain. Reversal after persistent crowding can be larger than the 0.10 percent pre-fee floor, but the mechanism cannot be tested honestly without the historical funding series.

## 3. Expected trade frequency per day per symbol

- Approximately 0 to 3 trades per day per symbol, depending on funding persistence and crowding frequency.

## 4. Expected failure modes

- Funding remains extreme during a strong trend and fading the crowd loses repeatedly.
- Funding observations are too sparse to reach 300 OOS trades.
- Funding timestamp alignment leaks information if the settlement value is used before it is known.
- Funding payments dominate price PnL around settlement.
- QC Lean v17685 does not provide native historical Binance USD-M funding data.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: historical funding rate with timestamps available before signal execution.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no / not confirmed by local data notes. Treat as blocked in v1 unless QC-native funding history is explicitly verified.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0006, or H0002. It does not use spot spread reclaim, liquidation wick geometry, same-symbol microtrend, Bollinger rejection, or BTC-to-ETH lead-lag. The mechanism is funding-crowding pressure in perpetual futures; its blocker is data availability, not duplication.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 2
- Total: 11

## 8. Decision

- [ ] Promote to hypothesis. Not selected because required historical funding data is not confirmed in QC Lean v17685.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0006_funding_regime_crowding.md`
      with reason. Never delete.
