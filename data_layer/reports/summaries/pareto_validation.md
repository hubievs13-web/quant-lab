# Pareto Validation (BTCUSDT vs ETHUSDT)

Generated: 2026-05-05 15:41 UTC. Binance only. Fee+slippage proxy = 0.18%.

## Decision

**RESEARCH CANDIDATE.**

Rule for `RESEARCH CANDIDATE`: both symbols need `n >= 80`, positive net after fees, `hit > 55%`, and `MFE/|MAE| >= 1.0`.

## Best common cell

| event | tf | h | BTC n | BTC fwd/net | BTC hit | BTC ratio | ETH n | ETH fwd/net | ETH hit | ETH ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| EV_FUND_EXTREME | 1h | h+72 | 156 | +1.10% / +0.92% | 56% | 1.37 | 136 | +0.98% / +0.80% | 60% | 1.23 |

## Main weakness

Cross-symbol stability achieved on the best common cell.
