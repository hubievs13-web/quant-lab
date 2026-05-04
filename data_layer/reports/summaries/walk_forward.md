# Walk-Forward Stability

Last refresh: 2026-05-04 15:23 UTC.
Splits each (symbol, tf, event_type, horizon) cell with `n >= 80` chronologically into 3 folds and reports per-fold net after taker (Tier T) and maker (Tier M) friction. A cell is `STABLE` if every fold's net has the same sign as the full-sample net.

Showing top 20 cells by `full_net_maker` (out of 85 with `n >= 80`).

| symbol | tf | event | h | n | net T | net M | T sign-stable | M sign-stable |
|---|---|---|---|---|---|---|---|---|
| ETHUSDT | 1h | FUND_FLIP | h+72 | 128 | +0.89% | +0.97% | 2/3 | 2/3 |
| ETHUSDT | 1h | VOL_BREAKOUT | h+72 | 80 | +0.50% | +0.58% | 1/3 | 2/3 |
| ETHUSDT | 1h | VOL_BREAKOUT | h+12 | 80 | +0.18% | +0.26% | 2/3 | 2/3 |
| BTCUSDT | 1h | FUND_FLIP | h+72 | 104 | +0.17% | +0.25% | 2/3 | 2/3 |
| BTCUSDT | 1h | FUND_FLIP | h+24 | 104 | +0.12% | +0.20% | 2/3 | yes |
| ETHUSDT | 1h | FUNDING_WINDOW_PRE | h+72 | 340 | +0.10% | +0.18% | 1/3 | 1/3 |
| ETHUSDT | 1h | VOL_BREAKOUT | h+24 | 80 | +0.01% | +0.09% | 1/3 | 1/3 |
| ETHUSDT | 1h | PREMIUM_COMPRESSION | h+12 | 157 | -0.00% | +0.08% | 2/3 | 1/3 |
| ETHUSDT | 5m | VOL_BREAKOUT | h+72 | 585 | -0.01% | +0.07% | 2/3 | 1/3 |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+72 | 255 | -0.01% | +0.07% | 1/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_COMPRESSION | h+24 | 157 | -0.02% | +0.06% | 2/3 | 1/3 |
| BTCUSDT | 5m | FUND_FLIP | h+72 | 104 | -0.03% | +0.05% | 2/3 | 2/3 |
| BTCUSDT | 1h | PREMIUM_COMPRESSION | h+12 | 156 | -0.04% | +0.04% | 1/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_SPIKE | h+12 | 246 | -0.04% | +0.04% | 1/3 | 2/3 |
| BTCUSDT | 1h | FUND_FLIP | h+12 | 104 | -0.04% | +0.04% | 2/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_SPIKE | h+24 | 244 | -0.07% | +0.01% | 2/3 | 1/3 |
| ETHUSDT | 1h | PREMIUM_SPIKE | h+3 | 247 | -0.08% | -0.00% | 2/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_COMPRESSION | h+3 | 157 | -0.10% | -0.02% | 2/3 | 2/3 |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+3 | 255 | -0.11% | -0.03% | yes | 2/3 |
| ETHUSDT | 1h | FUND_FLIP | h+3 | 128 | -0.11% | -0.03% | yes | 2/3 |
