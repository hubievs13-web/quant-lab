---
id: CE0025
slug: mark_premium_divergence_continuation
created: 2026-05-02
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0025 - mark_premium_divergence_continuation

## 1. Mechanism

When premium index and mark-last dislocation move in the same direction, the perp may be under persistent derivatives-side pressure rather than random last-trade noise. If last price begins moving with the pressure after both state variables align, a short continuation burst may occur as the perp catches up to the mark/premium state. This is a derivatives-state confirmation mechanism, not a generic price momentum rule.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.10 to 0.13 percent, but fragile.
- Reasoning from first principles: combined premium and mark pressure is closer to perp-specific leverage pressure than OHLCV alone, so a short continuation burst can plausibly clear 0.10 percent. However, continuation after confirmation may arrive late, creating adverse selection.

## 3. Expected trade frequency per day per symbol

- Expected combined BTCUSDT and ETHUSDT frequency: 5 to 15 trades per day.
- Per symbol: roughly 2 to 7 trades per day.

## 4. Expected failure modes

1. Confirmation happens only after the move is complete.
2. The mechanism is too close to ordinary short-horizon momentum if derivatives-state alignment is not strict.
3. Premium and mark pressure can reverse abruptly during liquidity shocks.
4. Signals cluster during macro moves and produce correlated drawdowns.
5. Average move fails to clear fees because next-bar execution misses the first burst.

## 5. Data required

- Bars: audited `um_klines_1m`.
- Derivatives features: audited `premium_index_klines`, `mark_price_klines`, `index_price_klines`.
- Availability: available in local audited TIER 1 data with DL0007 exception.
- DL0007 handling: exact missing price-state timestamps and dependent complete-source 5m bars are no-signal.
- QuantConnect native availability: not assumed; later QC use would require separate approval.

## 6. Distinct-from-rejected statement

This is not H0004 microtrend or H0005 compression breakout because it requires simultaneous derivatives-state pressure from premium and mark/index data, not just last-price continuation. It is not H0002 cross-asset lead-lag and not H0007 funding-clock timing. It is not H0001/H0006 spot mean reversion. The main concern is that the continuation leg could still behave like disguised momentum, so this candidate is parked.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 5
- Simplicity (1-5, higher is simpler): 3
- Risk of disguised rejected mechanism (1-5, higher is lower risk): 2
- Total: 16

## 8. Decision

- [ ] Promote to hypothesis as `Hxxxx_<slug>.md`.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0025_mark_premium_divergence_continuation.md` with reason.
