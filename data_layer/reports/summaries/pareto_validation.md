# Pareto Validation (BTCUSDT vs ETHUSDT)

Generated: 2026-05-04 15:11 UTC. Binance only. Fee+slippage proxy = 0.18%.

## Decision

**WATCHLIST ONLY.**

Rule for `RESEARCH CANDIDATE`: both symbols need `n >= 80`, positive net after fees, `hit > 55%`, and `MFE/|MAE| >= 1.0`.

## Best common cell

| event | tf | h | BTC n | BTC fwd/net | BTC hit | BTC ratio | ETH n | ETH fwd/net | ETH hit | ETH ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| EV_OI_SPIKE_UP | 1h | h+72 | 8 | +0.32% / +0.14% | 50% | 1.35 | 20 | +5.44% / +5.26% | 55% | 2.16 |

## Main weakness

The best event is not stable across both symbols after fees.
