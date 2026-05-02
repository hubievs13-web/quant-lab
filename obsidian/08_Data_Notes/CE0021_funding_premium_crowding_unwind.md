---
id: CE0021
slug: funding_premium_crowding_unwind
created: 2026-05-02
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
---

# CE0021 - funding_premium_crowding_unwind

## 1. Mechanism

Persistent positive or negative settled funding identifies a crowded leveraged side in Binance USD-M perpetuals. When the 1m premium index begins compressing against that crowded side while the perp last price has not fully repriced, the crowded side may be starting to unwind. The expected edge is not the funding timestamp itself; it is the combination of an already observable funding regime and a point-in-time premium reversal that indicates pressure is leaving the perp.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.18 percent.
- Reasoning from first principles: a true funding-plus-premium unwind can move the perp last price more than ordinary 5m noise because it reflects leveraged positioning pressure, not just OHLCV geometry. The 0.10 percent floor is plausible only when funding regime and premium compression agree; premium alone or funding clock alone is weaker.

## 3. Expected trade frequency per day per symbol

- Expected combined BTCUSDT and ETHUSDT frequency: 5 to 12 trades per day.
- Per symbol: roughly 2 to 6 trades per day, concentrated during persistent funding regimes with repeated premium compression attempts.

## 4. Expected failure modes

1. Strong trends keep funding and premium extreme for hours, so contrarian unwind entries fight continuation.
2. Premium compresses after last price has already moved, leaving no executable next-bar edge.
3. Funding regime is stale because settled funding updates every 8 hours and may not represent current positioning pressure.
4. Signals cluster across BTCUSDT and ETHUSDT during broad market deleveraging, creating correlated losses.
5. Raw move exists but average pre-fee edge is below 0.10 percent or cannot survive the 0.18 percent round-trip friction assumption.

## 5. Data required

- Bars: audited `um_klines_1m`, aggregated only from completed 1m rows into completed 5m rows if needed.
- Derivatives features: audited `funding_rate_history`, `premium_index_klines`, optional `mark_price_klines` and `index_price_klines` for state sanity checks.
- Availability: available in local audited TIER 1 data for BTCUSDT and ETHUSDT from 2024-01-01 to 2026-05-02T07:19:00Z.
- DL0007 handling: the exact missing price-state timestamps `2024-08-12T10:02:00Z` and `2024-08-12T10:03:00Z` are unavailable/no-signal; any dependent 5m bar requiring complete price-state data is also no-signal.
- QuantConnect native availability: not assumed. Later QC validation would require a separately approved custom-data path or verified native availability. This candidate does not authorize QC custom data.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, or H0006 because it is not spot spread reclaim, wick recovery, microtrend continuation, or Bollinger/range mean reversion. It is not H0002 because it does not use BTC-to-ETH residual lead-lag. It is not H0005 because it does not trade simple same-symbol compression breakout from OHLCV; premium compression is a derivatives state variable. It is not H0007 because it does not trade the scheduled funding-settlement clock or pre-settlement displacement; it uses actual settled funding regime only after timestamp availability plus premium pressure confirmation.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 5
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 5
- Simplicity (1-5, higher is simpler): 3
- Risk of disguised rejected mechanism (1-5, higher is lower risk): 4
- Total: 21

## 8. Decision

- [x] Promote to hypothesis as `H0008_funding_premium_crowding_unwind.md`.
- [ ] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0021_funding_premium_crowding_unwind.md` with reason.
