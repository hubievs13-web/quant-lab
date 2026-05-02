---
id: CE0023
slug: premium_compression_repricing
created: 2026-05-02
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0023 - premium_compression_repricing

## 1. Mechanism

The premium index measures perp pressure versus the reference index. When premium reaches an extreme and then compresses while last price lags the premium change, leveraged perp pressure may be unwinding before the OHLCV chart alone shows the repricing. The candidate trades the repricing of last price toward the changing premium state.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.10 to 0.14 percent.
- Reasoning from first principles: extreme premium compression can represent direct perp crowding pressure leaving the market and can plausibly move last price more than a normal 5m noise threshold. The edge floor is less defensible than CE0021 because premium alone lacks settled funding-regime context.

## 3. Expected trade frequency per day per symbol

- Expected combined BTCUSDT and ETHUSDT frequency: 6 to 14 trades per day.
- Per symbol: roughly 3 to 7 trades per day.

## 4. Expected failure modes

1. Premium normalizes without a tradeable last-price move.
2. Last price reprices before the next executable bar.
3. Premium extremes are trend-confirming rather than crowd-unwind signals.
4. The setup becomes disguised short-horizon mean reversion if premium is only used as a light filter.
5. Average raw movement is below the pre-fee edge floor.

## 5. Data required

- Bars: audited `um_klines_1m`.
- Derivatives features: audited `premium_index_klines`, optional `mark_price_klines` and `index_price_klines`.
- Availability: available in local audited TIER 1 data with DL0007 exception.
- DL0007 handling: exact missing price-state timestamps and dependent complete-source 5m bars are no-signal.
- QuantConnect native availability: not assumed; later QC use would require separate approval.

## 6. Distinct-from-rejected statement

This is not H0001/H0006 because the input is perp premium pressure, not a spot mean-reversion indicator. It is not H0004 or H0005 because it does not use only same-symbol OHLCV microtrend or compression breakout. It is not H0002 because there is no BTC-to-ETH lead-lag. It is not H0007 because it does not use scheduled funding settlement; no clock-only logic is present.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 5
- Simplicity (1-5, higher is simpler): 4
- Risk of disguised rejected mechanism (1-5, higher is lower risk): 3
- Total: 19

## 8. Decision

- [ ] Promote to hypothesis as `Hxxxx_<slug>.md`.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0023_premium_compression_repricing.md` with reason.
