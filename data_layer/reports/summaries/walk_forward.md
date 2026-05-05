# Walk-Forward Stability

Last refresh: 2026-05-05 15:41 UTC.
Splits each (symbol, tf, event_type, horizon) cell with `n >= 80` chronologically into 3 folds and reports per-fold net after taker (Tier T) and maker (Tier M) friction. A cell is `STABLE` if every fold's net has the same sign as the full-sample net.

Showing top 20 cells by `full_net_maker` (out of 108 with `n >= 80`).

| symbol | tf | event | h | n | net T | net M | T sign-stable | M sign-stable |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 1h | FUND_EXTREME | h+72 | 156 | +0.92% | +1.00% | yes | yes |
| ETHUSDT | 1h | FUND_EXTREME | h+72 | 136 | +0.80% | +0.88% | yes | yes |
| BTCUSDT | 1h | VOL_BREAKOUT | h+72 | 217 | +0.73% | +0.81% | yes | yes |
| BTCUSDT | 1h | FUND_FLIP | h+72 | 251 | +0.44% | +0.52% | 2/3 | 2/3 |
| ETHUSDT | 1h | VOL_BREAKOUT | h+72 | 208 | +0.40% | +0.48% | 2/3 | 2/3 |
| BTCUSDT | 1h | FUND_EXTREME | h+24 | 156 | +0.38% | +0.46% | yes | yes |
| BTCUSDT | 1h | VOL_BREAKOUT | h+24 | 217 | +0.25% | +0.33% | 2/3 | 2/3 |
| ETHUSDT | 1h | FUND_FLIP | h+72 | 257 | +0.22% | +0.30% | 2/3 | 2/3 |
| BTCUSDT | 1h | PREMIUM_COMPRESSION | h+72 | 517 | +0.21% | +0.29% | 2/3 | 2/3 |
| ETHUSDT | 1h | VOL_BREAKOUT | h+24 | 208 | +0.18% | +0.26% | 2/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_COMPRESSION | h+72 | 481 | +0.16% | +0.24% | 2/3 | 2/3 |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+72 | 703 | +0.13% | +0.21% | 2/3 | 2/3 |
| ETHUSDT | 1h | VOL_BREAKOUT | h+12 | 208 | +0.12% | +0.20% | 1/3 | 1/3 |
| BTCUSDT | 1h | FUND_FLIP | h+24 | 251 | +0.08% | +0.16% | 2/3 | 2/3 |
| ETHUSDT | 1h | FUNDING_WINDOW_PRE | h+72 | 431 | +0.08% | +0.16% | 2/3 | 2/3 |
| BTCUSDT | 1h | VOL_BREAKOUT | h+12 | 217 | +0.07% | +0.15% | 2/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_COMPRESSION | h+24 | 481 | +0.03% | +0.11% | 1/3 | 2/3 |
| ETHUSDT | 1h | FUND_EXTREME | h+24 | 136 | +0.02% | +0.10% | 2/3 | 2/3 |
| ETHUSDT | 1h | PREMIUM_SPIKE | h+72 | 724 | +0.01% | +0.09% | 1/3 | 1/3 |
| ETHUSDT | 1h | PREMIUM_COMPRESSION | h+12 | 481 | -0.05% | +0.03% | 2/3 | 2/3 |
