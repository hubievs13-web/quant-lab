---
id: CE0024
slug: derived_basis_extension_snapback
created: 2026-05-02
mechanism_class: basis
symbols: [BTCUSDT, ETHUSDT]
---

# CE0024 - derived_basis_extension_snapback

## 1. Mechanism

Derived basis can be measured from perp last price versus index price using audited `um_klines_1m` and `index_price_klines`. When derived basis extends sharply and then begins to contract, perp-specific pressure may unwind as last price converges toward index reference. This uses audited TIER 1 data rather than the blocked Binance basis endpoint history.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.09 to 0.13 percent.
- Reasoning from first principles: large perp-index basis moves can reflect leverage pressure, but the tradeable next-bar component may be small because index and perp prices often co-move quickly. The 0.10 percent floor is only marginally plausible and weaker than CE0021.

## 3. Expected trade frequency per day per symbol

- Expected combined BTCUSDT and ETHUSDT frequency: 5 to 12 trades per day if basis extension is defined only for notable dislocations.
- Per symbol: roughly 2 to 6 trades per day.

## 4. Expected failure modes

1. Derived basis contracts because index moves, not because perp pressure unwinds.
2. Perp-index spread is too small after friction.
3. Basis extension is a trend-confirming state, not a snapback state.
4. Index klines and last-trade klines align but do not represent executable spread capture.
5. The setup becomes ordinary last-price mean reversion if basis is not the causal variable.

## 5. Data required

- Bars: audited `um_klines_1m`.
- Derivatives features: audited `index_price_klines`; optional `mark_price_klines` and `premium_index_klines`.
- Availability: available in local audited TIER 1 data with DL0007 exception.
- DL0007 handling: exact missing price-state timestamps and dependent complete-source 5m bars are no-signal.
- Blocked data not used: Binance basis endpoint history is not used.

## 6. Distinct-from-rejected statement

This is not H0001/H0006 generic mean reversion because the state variable is derived perp-index basis, not a spot price band. It is not H0002 BTC-to-ETH lead-lag, H0004 microtrend, H0005 compression breakout, or H0007 funding-clock unwind. The risk is that it could degrade into ordinary mean reversion if basis is not sufficiently central; therefore it is parked rather than selected.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 2
- Data availability (1-5): 5
- Simplicity (1-5, higher is simpler): 4
- Risk of disguised rejected mechanism (1-5, higher is lower risk): 3
- Total: 17

## 8. Decision

- [ ] Promote to hypothesis as `Hxxxx_<slug>.md`.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0024_derived_basis_extension_snapback.md` with reason.
