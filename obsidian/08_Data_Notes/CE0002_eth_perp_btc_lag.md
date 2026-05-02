---
id: CE0002
slug: eth_perp_btc_lag
created: 2026-04-29
mechanism_class: lead_lag
symbols: [BTCUSDT, ETHUSDT]
---

# CE0002 - eth_perp_btc_lag

## 1. Mechanism

ETHUSDT perpetuals sometimes lead short-lived crypto beta moves during Ethereum-specific liquidation, staking, or alt-risk events. BTCUSDT may follow after ETH absorbs the first flow shock, but the BTC catch-up is usually smaller because BTC is deeper and less elastic. The candidate trades BTCUSDT in the direction of a completed ETHUSDT perp impulse.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.08 to 0.13 percent.
- Reasoning from first principles: ETH-specific flow can transmit to BTC through broad risk de-leveraging, but BTC depth dampens the follow-through. The upper end can clear the 0.10 percent floor only during strong ETH-led regimes, while the average may fall below the floor because BTC is less responsive than ETH.

## 3. Expected trade frequency per day per symbol

- BTCUSDT target trades: approximately 3 to 7 per day.
- ETHUSDT is used as the source signal and is not the traded leg in this candidate.

## 4. Expected failure modes

- ETH-specific events do not propagate to BTC, causing false BTC entries.
- BTC is already repriced by the time the ETH signal bar closes.
- Trade count may be too low if ETH-leading impulses are rare.
- The lower BTC beta leaves insufficient raw edge after 0.18 percent friction.
- Correlation flips during ETH idiosyncratic news.

## 5. Data required

- Bars: 5m TradeBar data for ETHUSDT and BTCUSDT Binance USD-M Futures.
- Derivatives features: none beyond perpetual futures bar prices and volume if available.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: partial. Minute bar data is expected per local data notes, but exact QC symbol mapping must be verified before implementation.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not a spot mean-reversion setup like H0001 or H0006, and it does not use wick-based liquidation proxies like H0003. It also differs from H0004 because it does not trade same-symbol BTC microtrend; it requires ETH perpetual futures to lead and BTC perpetual futures to react later, with delayed target execution.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 2
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 4
- Total: 13

## 8. Decision

- [ ] Promote to hypothesis. Not selected in this researcher pass because expected average edge may fall below the 0.10 percent floor.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0002_eth_perp_btc_lag.md`
      with reason. Never delete.
