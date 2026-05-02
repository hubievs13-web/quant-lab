---
id: CE0014
slug: mark_index_premium_snapback
created: 2026-05-01
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0014 - mark_index_premium_snapback

## 1. Mechanism

Perpetual contracts can diverge from mark or index value when leveraged demand becomes one-sided. If a rich premium begins compressing, longs may be crowded and vulnerable to unwind; if a discount begins compressing, shorts may be crowded. The edge would trade the direction of premium normalization rather than raw price reversal.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.25 percent if mark/index/premium history is available.
- Reasoning from first principles: basis and premium are futures-specific pressure variables. A measurable premium snapback can identify leverage imbalance directly and can plausibly exceed 0.10 percent before fees, but only with real timestamp-aligned premium data.

## 3. Expected trade frequency per day per symbol

- Approximately 1 to 5 trades per day per symbol, depending on how often premium dislocations occur.

## 4. Expected failure modes

- Premium remains extreme during persistent directional regimes.
- Premium compression happens before the next executable futures bar.
- QC does not provide historical mark/index/premium data for Binance USD-M Futures.
- A spot or index proxy introduces external data requirements outside v1.
- Trade frequency is too low after requiring large enough dislocations.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: historical mark price, index price, premium index, or basis series.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no / not confirmed by local data notes. Treat as BLOCKED unless QC-native premium or mark/index history is explicitly verified.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, H0006, or H0002. It is not a spread reclaim on spot, wick recovery, microtrend, compression breakout, Bollinger fade, or BTC-to-ETH lag. The mechanism is perpetual premium dislocation versus reference value, but it is blocked because the repository data notes do not confirm the required QC-native basis data.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 2
- Total: 11

## 8. Decision

- [ ] Promote to hypothesis. BLOCKED because required basis / premium data is not confirmed in QC Lean v17685.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0014_mark_index_premium_snapback.md`
      with reason. Never delete.
