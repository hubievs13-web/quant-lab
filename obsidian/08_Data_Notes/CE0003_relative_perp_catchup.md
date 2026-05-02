---
id: CE0003
slug: relative_perp_catchup
created: 2026-04-29
mechanism_class: lead_lag
symbols: [BTCUSDT, ETHUSDT]
---

# CE0003 - relative_perp_catchup

## 1. Mechanism

When BTCUSDT and ETHUSDT perpetuals normally move together but one leg sharply underreacts to a completed move in the other, the lagging leg may catch up as cross-crypto hedges are rebalanced. The edge is directional catch-up in the lagging perpetual, not spread mean reversion to a statistical average. It uses completed bars only and waits for the next bar before execution.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.10 to 0.15 percent.
- Reasoning from first principles: the opportunity is the short delay in beta transmission between two highly liquid perpetual contracts. The edge could clear the floor when one leg has a large completed impulse and the other has not yet reflected its usual beta, but the expected edge is fragile because both contracts are highly efficient.

## 3. Expected trade frequency per day per symbol

- Approximately 4 to 8 trades per day across BTCUSDT and ETHUSDT combined.

## 4. Expected failure modes

- The apparent underreaction is a real beta regime shift, not a lag.
- Both contracts catch up inside the same 5m bar, leaving no executable edge.
- Parameter count can grow if the beta definition is made too flexible.
- Trading both directions can increase churn and cost drag.
- Missing or mismatched bars can create false relative-return gaps.

## 5. Data required

- Bars: 5m TradeBar data for BTCUSDT and ETHUSDT Binance USD-M Futures.
- Derivatives features: none beyond perpetual futures bar prices.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: partial. Expected per local data notes, but exact futures symbol support must be verified in QC.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001 or H0006 because it is not fading a same-symbol spot spread, band touch, or range event. It is not H0003 because it does not proxy liquidations from candle wicks. It is not H0004 because the signal is a cross-perpetual relative lag after a completed move, not same-symbol BTC microtrend continuation with a trailing exit.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 3
- Total: 13

## 8. Decision

- [ ] Promote to hypothesis. Not selected in this researcher pass because the mechanism is less direct than CE0001 and has more beta-definition complexity.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0003_relative_perp_catchup.md`
      with reason. Never delete.
