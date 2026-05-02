---
id: CE0005
slug: funding_extreme_reversal
created: 2026-04-29
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
---

# CE0005 - funding_extreme_reversal

## 1. Mechanism

Extreme positive funding can indicate crowded long positioning in perpetual futures, while extreme negative funding can indicate crowded short positioning. After the crowding signal is known, price may mean-revert as leveraged positions reduce exposure or as contrarian liquidity earns the funding premium. The candidate would fade the crowded side after a completed funding observation.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.25 percent if reliable historical funding data is available.
- Reasoning from first principles: funding extremes are directly tied to perpetual-specific positioning pressure and can identify a crowding premium not present in spot-only data. However, without historical funding data inside QC, the edge cannot be tested honestly in v1.

## 3. Expected trade frequency per day per symbol

- Approximately 0 to 3 trades per day per symbol, depending on funding threshold and whether entries are allowed only near 8-hour funding settlements.

## 4. Expected failure modes

- Funding remains extreme during persistent trends, causing repeated contrarian losses.
- Funding observations are too sparse to reach 300 OOS trades.
- Funding payments and price PnL interact unfavorably around settlement.
- QC lacks native historical funding data for Binance USD-M Futures.
- Using price-only proxies for funding would fabricate the required data.

## 5. Data required

- Bars: 5m TradeBar data for BTCUSDT and ETHUSDT Binance USD-M Futures.
- Derivatives features: historical 8-hour funding rate series with timestamps available before signal execution.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no / not confirmed by local data notes. Historical funding as a native QC dataset is not confirmed and must be treated as unavailable in v1 unless explicitly verified before implementation.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is structurally different from H0001, H0003, H0004, and H0006 because it uses perpetual funding crowding rather than spot spread reclaim, wick geometry, same-symbol microtrend, or Bollinger mean reversion. The issue is not duplication; the issue is data availability in the current v1 Obsidian-only and QC-native workflow.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 2
- Total: 11

## 8. Decision

- [ ] Promote to hypothesis. Not selected in this researcher pass because required historical funding data is not confirmed in QC Lean v17685.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0005_funding_extreme_reversal.md`
      with reason. Never delete.
