# Permutation Test

Last refresh: 2026-05-04 15:05 UTC.
Bootstrap test: for each cell with `n >= 80` we draw 1000 random samples of the same size from the underlying bar-level forward-return universe at the matching horizon and compute the two-tailed p-value `(1 + #{|perm_mean| >= |obs_mean|}) / (n_perms + 1)`. A cell is `PASS` when `p_value <= 0.05`.

Showing top 20 cells by p-value (out of 85; 3 cells PASS at p<=0.05).

| symbol | tf | event | h | n | obs net T | obs net M | p-value | verdict |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5m | VOL_BREAKOUT | h+72 | 512 | -0.32% | -0.24% | 0.006 | PASS |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+1 | 2224 | -0.17% | -0.09% | 0.017 | PASS |
| ETHUSDT | 5m | VOL_BREAKOUT | h+72 | 585 | -0.01% | +0.07% | 0.032 | PASS |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+1 | 256 | -0.13% | -0.05% | 0.070 | FAIL |
| ETHUSDT | 5m | VOL_BREAKOUT | h+1 | 587 | -0.16% | -0.08% | 0.078 | FAIL |
| BTCUSDT | 5m | VOL_BREAKOUT | h+12 | 512 | -0.21% | -0.13% | 0.081 | FAIL |
| ETHUSDT | 5m | FUND_FLIP | h+72 | 128 | -0.44% | -0.36% | 0.105 | FAIL |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+3 | 2224 | -0.17% | -0.09% | 0.120 | FAIL |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+3 | 255 | -0.11% | -0.03% | 0.135 | FAIL |
| ETHUSDT | 1h | FUND_FLIP | h+72 | 128 | +0.89% | +0.97% | 0.140 | FAIL |
| BTCUSDT | 5m | FUND_FLIP | h+72 | 104 | -0.03% | +0.05% | 0.152 | FAIL |
| BTCUSDT | 1h | FUND_FLIP | h+24 | 104 | +0.12% | +0.20% | 0.159 | FAIL |
| ETHUSDT | 5m | PREMIUM_COMPRESSION | h+12 | 2132 | -0.16% | -0.08% | 0.160 | FAIL |
| ETHUSDT | 5m | PREMIUM_SPIKE | h+72 | 3055 | -0.12% | -0.04% | 0.175 | FAIL |
| BTCUSDT | 5m | FUND_FLIP | h+1 | 104 | -0.16% | -0.08% | 0.192 | FAIL |
| ETHUSDT | 1h | VOL_BREAKOUT | h+1 | 80 | -0.28% | -0.20% | 0.207 | FAIL |
| ETHUSDT | 1h | PREMIUM_SPIKE | h+3 | 247 | -0.08% | -0.00% | 0.222 | FAIL |
| ETHUSDT | 1h | VOL_BREAKOUT | h+12 | 80 | +0.18% | +0.26% | 0.222 | FAIL |
| ETHUSDT | 5m | VOL_BREAKOUT | h+12 | 587 | -0.14% | -0.06% | 0.228 | FAIL |
| BTCUSDT | 1h | PREMIUM_COMPRESSION | h+12 | 156 | -0.04% | +0.04% | 0.256 | FAIL |
