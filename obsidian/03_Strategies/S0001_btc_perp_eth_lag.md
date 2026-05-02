---
id: S0001
hypothesis: H0002
slug: btc_perp_eth_lag
created: 2026-04-29
status: draft
---

# S0001 - btc_perp_eth_lag (implements H0002)

## 1. Link to hypothesis

`obsidian/02_Hypotheses/H0002_btc_perp_eth_lag.md`

## 2. Strategy folder

`strategies/H0002_btc_perp_eth_lag/`

## 3. Files

- `strategies/H0002_btc_perp_eth_lag/main.py`
- `strategies/H0002_btc_perp_eth_lag/README.md`
- `strategies/H0002_btc_perp_eth_lag/diagnostics.md`

## 4. Mechanism summary

BTCUSDT perpetual futures can lead short crypto risk-transfer moves. H0002 trades ETHUSDT perpetual futures only after a completed BTCUSDT 5m impulse if ETHUSDT has not already moved enough in the same completed 5m bar. The position is held for exactly 3 completed ETHUSDT 5m bars.

## 5. Parameters

| Name | Value |
|------|-------|
| btc_impulse_pct | 0.35 percent |
| eth_max_samebar_move_pct | 0.12 percent |
| hold_bars | 3 |

## 6. QC status

Ready for manual QuantConnect smoke test only after the user verifies Binance USD-M Futures symbol mapping and brokerage support. If QC cannot provide BTCUSDT and ETHUSDT futures/perpetual 5m bars, the strategy is BLOCKED and must not be replaced with spot data.
