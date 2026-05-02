---
id: CE0016
slug: predicted_funding_flip_repricing
created: 2026-05-01
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
---

# CE0016 - predicted_funding_flip_repricing

## 1. Mechanism

Binance USD-M perpetual traders react not only to settled funding, but also to the currently predicted funding direction before the next settlement. A sharp predicted funding flip from positive to negative can indicate that long-side demand has collapsed or short pressure has become dominant; a flip from negative to positive can indicate the reverse. The candidate would trade the repricing that follows a confirmed funding forecast regime change, not a scheduled settlement clock effect.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.25 percent if timestamped predicted funding or premium-index data is available.
- Reasoning from first principles: predicted funding changes are a direct perpetual-specific crowding variable. A true sign flip in expected transfer payments can force leveraged inventory adjustment large enough to clear the 0.10 percent pre-fee floor. Without the actual predicted funding or premium input, the edge is not testable and must not be proxied with price-only bars.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 0 to 3 trades per day.
- ETHUSDT: approximately 0 to 3 trades per day.
- Combined: approximately 2 to 8 trades per day when funding forecasts flip or compress sharply.

## 4. Expected failure modes

- Funding forecast flips are too rare to reach 300 OOS trades.
- The funding forecast flips after price has already moved, leaving no next-bar edge.
- Persistent directional trends keep funding in one regime and punish contrarian entries.
- Funding timestamps are delayed or revised, creating leakage risk if modeled incorrectly.
- Funding transfer magnitude is too small on BTCUSDT and ETHUSDT to overcome 0.18 percent round-trip friction.

## 5. Data required

- Bars: 1m or 5m Binance USD-M Futures OHLCV bars for BTCUSDT and ETHUSDT.
- Derivatives features: predicted funding rate, premium index, or another timestamped exchange-native funding forecast observable before execution.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: BLOCKED. Local data notes say historical 8-hour funding-rate series is not confirmed as native QC data; predicted funding or premium-index history is also not confirmed.
- If unavailable: this candidate is blocked until a Phase 2 data layer or a verified QC-native dataset is approved. Do not proxy predicted funding with price bars or scheduled settlement times.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, or H0006 because it does not use spot spread reclaim, wick geometry, same-symbol microtrend, compression breakout, or Bollinger/range mean reversion. It is not H0002 because it does not trade ETH from a BTC price impulse. It is not funding settlement unwind because it requires an actual predicted funding or premium-index state transition and does not infer pressure from the settlement clock or pre-settlement displacement.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Code complexity, lower is better (1-5): 3
- Risk of disguised rejected mechanism, lower is better (1-5): 1
- Total: 13

## 8. Decision

- [ ] Promote to hypothesis.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0016_predicted_funding_flip_repricing.md` with reason.

Researcher decision: BLOCKED. The mechanism is plausible and futures-specific, but required predicted funding / premium data is not confirmed as QC-native in Lean v17685.
