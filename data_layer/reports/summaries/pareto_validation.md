# Pareto Validation (BTCUSDT vs ETHUSDT)

Generated: 2026-05-04 13:34 UTC. Binance only. Fee+slippage proxy = 0.18%.

## Decision

**WATCHLIST ONLY.**

Rule for `RESEARCH CANDIDATE`: both symbols need `n >= 80`, positive net after fees, `hit > 55%`, and `MFE/|MAE| >= 1.0`.

## Best common cell

| event | tf | h | BTC n | BTC fwd/net | BTC hit | BTC ratio | ETH n | ETH fwd/net | ETH hit | ETH ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| EV_FUND_EXTREME | 1h | h+72 | 22 | +1.29% / +1.11% | 64% | 2.43 | 20 | +0.13% / -0.05% | 55% | 1.11 |

## Main weakness

The best event is not stable across both symbols after fees.
