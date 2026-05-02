---
id: CE0018
slug: mark_last_stop_trigger_dislocation
created: 2026-05-01
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0018 - mark_last_stop_trigger_dislocation

## 1. Mechanism

Perpetual futures risk engines and many liquidation or stop-trigger calculations reference mark price rather than last trade price. When last price runs away from mark price and then mark begins catching up, stop-trigger pressure can appear in the direction of mark convergence. The candidate would trade only when a mark-last dislocation indicates a futures-specific trigger-pressure zone.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.20 percent if mark price and last price history are available.
- Reasoning from first principles: mark-last divergence is a direct derivatives microstructure variable. If stop-trigger pressure concentrates as mark catches up, short bursts can plausibly exceed the 0.10 percent pre-fee floor. With last-price OHLCV alone, the mechanism cannot be observed.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 1 to 4 trades per day.
- ETHUSDT: approximately 2 to 6 trades per day.
- Combined: approximately 4 to 10 trades per day during volatile sessions.

## 4. Expected failure modes

- Mark-last dislocations are too small on BTCUSDT and ETHUSDT to matter after friction.
- Mark price catches up without tradable last-price continuation.
- Exchange mark-price updates are not timestamped cleanly enough for no-leakage testing.
- The effect is concentrated in rare stress periods and does not reach 300 OOS trades.
- QC does not provide historical mark price for Binance USD-M Futures.

## 5. Data required

- Bars: 1m or 5m Binance USD-M Futures OHLCV bars for BTCUSDT and ETHUSDT.
- Derivatives features: historical mark price and last trade price, timestamp-aligned before execution.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: BLOCKED. Local notes do not confirm QC-native historical mark/index/premium data for Binance USD-M Futures.
- If unavailable: this candidate is blocked. Do not replace mark price with futures close or candle mid.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, H0006, or H0002 because it does not use spot spread reclaim, liquidation-wick proxying, same-symbol microtrend, compression breakout, Bollinger mean reversion, or BTC-to-ETH lag. It is also not funding settlement unwind because it has no scheduled funding event; the mechanism is mark-price trigger pressure specific to perpetual futures.

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
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0018_mark_last_stop_trigger_dislocation.md` with reason.

Researcher decision: BLOCKED. Required mark-price history is not confirmed as QC-native.
