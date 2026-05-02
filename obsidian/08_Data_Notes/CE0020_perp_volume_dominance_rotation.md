---
id: CE0020
slug: perp_volume_dominance_rotation
created: 2026-05-01
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
---

# CE0020 - perp_volume_dominance_rotation

## 1. Mechanism

During short intraday rotations, leveraged attention can move from BTCUSDT to ETHUSDT or back as traders switch the contract used for risk transfer. A relative futures-volume surge in one contract without a corresponding price displacement in the other could signal upcoming cross-market attention rotation. The candidate would trade the contract receiving new relative derivatives activity, not simply the one with a larger price bar.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.06 to 0.11 percent.
- Reasoning from first principles: relative volume dominance is a weaker proxy than OI, funding, basis, mark, or signed taker flow. It might occasionally identify leverage attention shifts, but ordinary volume does not identify direction or crowding cleanly enough. Clearing the 0.10 percent pre-fee floor is not plausible on average without additional futures state data.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 2 to 5 trades per day.
- ETHUSDT: approximately 3 to 7 trades per day.
- Combined: approximately 5 to 12 trades per day if futures bar volume is present and stable.

## 4. Expected failure modes

- Relative volume surge reflects completed activity, not future rotation.
- Bar volume lacks direction, so entries become disguised price momentum or noise.
- QC futures volume fields may be missing, inconsistent, or not comparable across BTCUSDT and ETHUSDT.
- Adding enough filters to make the signal directional would exceed the 3-parameter limit.
- Average raw move falls below 0.18 percent round-trip friction.

## 5. Data required

- Bars: 5m Binance USD-M Futures OHLCV bars for BTCUSDT and ETHUSDT.
- Derivatives features: futures bar volume for both symbols; no funding, OI, basis, mark, order book, or liquidation data.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: PARTIAL. Price bars are expected per local notes; futures bar volume must be verified in QC and is not enough to prove direction.
- If unavailable: this candidate is blocked. If available, it is still rejected at researcher stage because the pre-fee edge floor is weak.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0005, H0006, or funding settlement unwind because it does not use spread reclaim, wick recovery, compression breakout, Bollinger/range mean reversion, or the funding clock. It is not the same as H0002 because it does not trade ETH from a BTC price impulse; it tries to identify relative derivatives attention through volume. It remains risky because, without signed flow or OI, the mechanism can collapse into a disguised version of H0004-style short-horizon price continuation.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 2
- Probability of clearing pre-fee floor (1-5): 1
- Data availability (1-5): 3
- Code complexity, lower is better (1-5): 3
- Risk of disguised rejected mechanism, lower is better (1-5): 4
- Total: 13

## 8. Decision

- [ ] Promote to hypothesis.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0020_perp_volume_dominance_rotation.md` with reason.

Researcher decision: REJECTED at researcher stage. The data may be partially available, but expected average pre-fee edge is not honestly above 0.10 percent and the mechanism risks collapsing into rejected price-pattern momentum.
