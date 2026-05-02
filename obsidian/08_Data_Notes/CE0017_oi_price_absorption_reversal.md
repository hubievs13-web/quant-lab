---
id: CE0017
slug: oi_price_absorption_reversal
created: 2026-05-01
mechanism_class: oi
symbols: [BTCUSDT, ETHUSDT]
---

# CE0017 - oi_price_absorption_reversal

## 1. Mechanism

When open interest rises sharply while price fails to extend, new leveraged positions may be absorbed by passive liquidity instead of starting a trend. If aggressive new longs are absorbed near the high, a short reversal can follow as those positions exit; if aggressive new shorts are absorbed near the low, a long reversal can follow. The edge is the failure of fresh leverage to move price, not a generic candle reversal.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.22 percent if 5m or faster OI snapshots are available.
- Reasoning from first principles: OI expansion without price progress can identify trapped leveraged inventory. Forced exit of trapped positions can plausibly create a next-bar move above the 0.10 percent pre-fee floor, especially on ETHUSDT where liquidity is thinner than BTCUSDT. Without OI, the absorption state cannot be distinguished from ordinary low-volatility chop.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 1 to 4 trades per day.
- ETHUSDT: approximately 2 to 5 trades per day.
- Combined: approximately 4 to 9 trades per day if OI snapshots are available and timestamp-aligned.

## 4. Expected failure modes

- Rising OI with flat price is accumulation before continuation, not trapped flow.
- OI snapshots are too slow and arrive after the reversal already occurred.
- The signal needs additional filters to separate absorption from continuation, exceeding the 3-parameter limit.
- Trade count falls below 300 OOS after strict OI timestamp alignment.
- QC lacks native historical OI for Binance USD-M Futures.

## 5. Data required

- Bars: 5m Binance USD-M Futures OHLCV bars for BTCUSDT and ETHUSDT.
- Derivatives features: historical open interest snapshots with timestamps known before signal execution.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: BLOCKED. Local data notes state native OI history for Binance USD-M Futures is not confirmed.
- If unavailable: this candidate is blocked. Do not proxy OI with volume, candle range, or consecutive bars.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, or H0006 because it does not trade spread reclaim, wick recovery, price microtrend, compression breakout, or Bollinger/range rejection. It is not H0002 because it is not BTC-to-ETH lead-lag. It is not funding settlement unwind because it does not use the funding clock; the required state variable is timestamped OI expansion with price absorption.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Code complexity, lower is better (1-5): 3
- Risk of disguised rejected mechanism, lower is better (1-5): 2
- Total: 14

## 8. Decision

- [ ] Promote to hypothesis.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0017_oi_price_absorption_reversal.md` with reason.

Researcher decision: BLOCKED. It requires QC-native historical OI, which is not confirmed in Lean v17685.
