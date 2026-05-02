---
id: CE0001
slug: btc_perp_eth_lag
created: 2026-04-29
mechanism_class: lead_lag
symbols: [BTCUSDT, ETHUSDT]
---

# CE0001 - btc_perp_eth_lag

## 1. Mechanism

BTCUSDT perpetual futures are the deepest crypto risk-transfer instrument on Binance USD-M. Fast directional BTC perp moves can force cross-crypto delta adjustment before ETHUSDT has fully repriced, especially during short intraday risk bursts. The edge is to trade ETHUSDT in the direction of a BTCUSDT perp impulse only after the BTC signal bar is complete, expecting ETH to catch up over the next few minutes.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.18 percent.
- Reasoning from first principles: the entry is not generic same-symbol momentum. It targets delayed cross-asset repricing after BTC perp flow shocks, where ETH often reacts with a short lag because BTC is the first instrument used for portfolio risk adjustment. The expected move must be large enough to survive the 0.18 percent round-trip friction after testing; a priori, the raw move target is modest but above the 0.10 percent pre-fee floor because ETH beta to a BTC 5m impulse can exceed 0.3 percent in active sessions.

## 3. Expected trade frequency per day per symbol

- ETHUSDT target trades: approximately 5 to 10 per day when BTC 5m impulse filters are active.
- BTCUSDT is used as the source signal and is not the traded leg in this candidate.

## 4. Expected failure modes

- ETH reprices in the same bar as BTC, so delayed execution captures no remaining move.
- BTC impulse is news-driven and ETH beta decouples, creating adverse selection.
- Signal clusters during high volatility and repeated entries overtrade the same impulse.
- Round-trip friction of approximately 0.18 percent consumes the raw lag effect.
- Timestamp alignment between BTCUSDT and ETHUSDT bars is incomplete in QC, reducing valid signals.

## 5. Data required

- Bars: 5m TradeBar data for BTCUSDT and ETHUSDT Binance USD-M Futures.
- Derivatives features: none beyond perpetual futures bar prices and volume if available.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: partial. Minute bar data for BTCUSDT and ETHUSDT perpetuals is expected via the Crypto Futures dataset per local data notes, but the engineer must verify the exact Binance Futures symbol mapping in QuantConnect before implementation.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001 or H0006 because it does not fade a same-symbol spot dislocation or Bollinger/range event. It is not H0003 because it does not infer liquidations from wick geometry and does not require liquidation data. It is not H0004 because it does not trade BTC same-symbol microtrend with a trailing stop; the mechanism is cross-asset lead-lag from BTC perpetual futures flow into ETH perpetual futures with delayed execution on the target symbol.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 4
- Total: 15

## 8. Decision

- [x] Promote to hypothesis as `H0002_btc_perp_eth_lag.md`.
- [ ] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0001_btc_perp_eth_lag.md`
      with reason. Never delete.
