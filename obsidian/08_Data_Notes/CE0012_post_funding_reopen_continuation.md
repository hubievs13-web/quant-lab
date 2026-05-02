---
id: CE0012
slug: post_funding_reopen_continuation
created: 2026-05-01
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
---

# CE0012 - post_funding_reopen_continuation

## 1. Mechanism

After a scheduled Binance USD-M funding settlement, traders who reduced exposure to avoid funding may reopen positions. If the first completed post-settlement 5m bar is directionally strong, the next few bars may continue as delayed re-entry flow joins the move. This is futures-specific because the event clock is the perpetual funding settlement schedule, not a generic time-of-day momentum rule.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.08 to 0.13 percent.
- Reasoning from first principles: post-settlement reopening can create short continuation when sidelined leveraged flow returns. However, without historical funding rates, the signal cannot tell whether funding was large enough to motivate position reduction, so the average edge may sit below the 0.10 percent floor.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 1 to 3 trades per day.
- ETHUSDT: approximately 1 to 3 trades per day.
- Combined: approximately 4 to 10 trades per day if both symbols are traded around the three daily funding settlements.

## 4. Expected failure modes

- The first post-settlement move is exhaustion, not continuation.
- Reopening flow is only meaningful when funding is extreme, and funding history is not available in v1.
- Same-symbol continuation after one strong bar is too close to ordinary short-horizon momentum and may not survive costs.
- News around settlement timestamps dominates the funding-calendar effect.
- Signals across BTCUSDT and ETHUSDT are highly correlated and increase drawdown.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: scheduled funding settlement timestamps only. Historical funding rate values would improve the mechanism but are not available in v1 and are not assumed.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: partial / expected for futures price bars, with exact symbol support requiring verification. Historical funding values are not required by the bar-only version.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0006, H0005, or H0002 because it does not use spot mean reversion, liquidation wick geometry, Bollinger rejection, compression breakout, or BTC-to-ETH lead-lag. It has some risk of resembling H0004 because it trades same-symbol continuation, but the proposed trigger is confined to the perpetual funding settlement event rather than a generic 1m microtrend count.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 2
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 4
- Total: 13

## 8. Decision

- [ ] Promote to hypothesis. Not selected because the pre-fee edge floor is only weakly justified without actual funding-rate history.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0012_post_funding_reopen_continuation.md`
      with reason. Never delete.
