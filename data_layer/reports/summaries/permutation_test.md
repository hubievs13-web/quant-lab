# Permutation Test

Last refresh: 2026-05-05 16:09 UTC.
Bootstrap test: for each cell with `n >= 80` we draw 1000 random samples of the same size from the underlying bar-level forward-return universe at the matching horizon and compute the two-tailed p-value `(1 + #{|perm_mean| >= |obs_mean|}) / (n_perms + 1)`. A cell is `PASS` when `p_value <= 0.05`.

Showing top 20 cells by p-value (out of 108; 9 cells PASS at p<=0.05).

| symbol | tf | event | h | n | obs net T | obs net M | p-value | verdict |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+3 | 6620 | -0.17% | -0.09% | 0.001 | PASS |
| BTCUSDT | 5m | VOL_BREAKOUT | h+1 | 1538 | -0.17% | -0.09% | 0.003 | PASS |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+1 | 6620 | -0.17% | -0.09% | 0.007 | PASS |
| BTCUSDT | 5m | FUND_EXTREME | h+3 | 156 | -0.13% | -0.05% | 0.014 | PASS |
| BTCUSDT | 1h | FUND_EXTREME | h+24 | 156 | +0.38% | +0.46% | 0.015 | PASS |
| BTCUSDT | 1h | FUND_EXTREME | h+72 | 156 | +0.92% | +1.00% | 0.021 | PASS |
| BTCUSDT | 1h | VOL_BREAKOUT | h+72 | 217 | +0.73% | +0.81% | 0.029 | PASS |
| BTCUSDT | 1h | VOL_BREAKOUT | h+24 | 217 | +0.25% | +0.33% | 0.039 | PASS |
| ETHUSDT | 5m | VOL_BREAKOUT | h+72 | 1718 | -0.09% | -0.01% | 0.045 | PASS |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+3 | 703 | -0.11% | -0.03% | 0.061 | FAIL |
| BTCUSDT | 1h | VOL_BREAKOUT | h+12 | 217 | +0.07% | +0.15% | 0.063 | FAIL |
| ETHUSDT | 1h | FUND_EXTREME | h+72 | 136 | +0.80% | +0.88% | 0.066 | FAIL |
| ETHUSDT | 1h | VOL_BREAKOUT | h+12 | 208 | +0.12% | +0.20% | 0.084 | FAIL |
| BTCUSDT | 5m | VOL_BREAKOUT | h+72 | 1538 | -0.11% | -0.03% | 0.106 | FAIL |
| BTCUSDT | 5m | VOL_BREAKOUT | h+3 | 1538 | -0.17% | -0.09% | 0.110 | FAIL |
| ETHUSDT | 5m | FUND_FLIP | h+72 | 257 | -0.34% | -0.26% | 0.128 | FAIL |
| BTCUSDT | 1h | PREMIUM_COMPRESSION | h+3 | 518 | -0.12% | -0.04% | 0.136 | FAIL |
| BTCUSDT | 1h | FUND_FLIP | h+72 | 251 | +0.44% | +0.52% | 0.138 | FAIL |
| ETHUSDT | 1h | VOL_BREAKOUT | h+24 | 208 | +0.18% | +0.26% | 0.141 | FAIL |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+1 | 704 | -0.15% | -0.07% | 0.143 | FAIL |
