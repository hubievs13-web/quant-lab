---
id: L0002
slug: simple_btc_eth_perp_lead_lag_failed
created: 2026-04-29
related_hypotheses: [H0002]
---

# L0002 - simple_btc_eth_perp_lead_lag_failed

## Claim

Simple BTCUSDT to ETHUSDT 5m perpetual lead-lag without an independent regime mechanism did not produce a valid intraday edge under Falsification Framework V3.

## Evidence

H0002 / S0001 / BT0001 ran a full QuantConnect backtest for 2024-01-01 to 2025-01-01. The run ended with -14.608% net profit, Sharpe -0.774, 28.3% drawdown, 31% win rate, 132 completed trades, 43.07 USDT in fees, and negative expectancy of -0.098. Devin verdict: FAIL / REJECTED. Monte Carlo was not run because criteria 1-6 failed.

## Implication for future hypotheses

Do not repeat the same BTC 5m impulse to ETH residual catch-up mechanism with different thresholds, different hold bars, leverage changes, stop-losses, take-profits, cooldowns, or simple filters. A future BTC/ETH futures hypothesis must use a genuinely different mechanism, such as funding, open interest, basis/funding dislocation, volatility regime transition, or an independently defined higher-timeframe futures regime.

## Anti-pattern

Changing `btc_impulse_pct`, `eth_max_samebar_move_pct`, `hold_bars`, leverage, or adding a stop-loss / take-profit / time filter / cooldown to H0002 is tuning a failed backtest, not new research.
