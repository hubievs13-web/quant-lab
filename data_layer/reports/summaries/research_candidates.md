# Research Candidates

Last refresh: 2026-05-05 15:41 UTC.
Cells that pass every stability gate at once. Tier T uses `p <= 0.05`; Tier M uses `p <= 0.10` (relaxed while only 365 days of data are available). All rows already require `n >= 80` and walk-forward sign stability for the matching tier. **Long sections** list cells with a stable positive net; trade in the direction implied by the event. **Fade sections** list cells with a stable *negative* net; the hypothesis must declare `direction: fade` and trade against the event. Source: `walk_forward.md` + `permutation_test.md`.

## Cross-symbol Pareto + stability (highest grade)

| tier | dir | tf | event | h | BTC n | BTC net | BTC p | ETH n | ETH net | ETH p |
|---|---|---|---|---|---|---|---|---|---|---|
| M | long | 1h | FUND_EXTREME | h+72 | 156 | +1.00% | 0.021 | 136 | +0.88% | 0.066 |

## Tier T long candidates (`p <= 0.05`)

| symbol | tf | event | h | n | net | p-value |
|---|---|---|---|---|---|---|
| BTCUSDT | 1h | FUND_EXTREME | h+72 | 156 | +0.92% | 0.021 |
| BTCUSDT | 1h | VOL_BREAKOUT | h+72 | 217 | +0.73% | 0.029 |
| BTCUSDT | 1h | FUND_EXTREME | h+24 | 156 | +0.38% | 0.015 |

## Tier M long candidates (`p <= 0.10`)

| symbol | tf | event | h | n | net | p-value |
|---|---|---|---|---|---|---|
| BTCUSDT | 1h | FUND_EXTREME | h+72 | 156 | +1.00% | 0.021 |
| ETHUSDT | 1h | FUND_EXTREME | h+72 | 136 | +0.88% | 0.066 |
| BTCUSDT | 1h | VOL_BREAKOUT | h+72 | 217 | +0.81% | 0.029 |
| BTCUSDT | 1h | FUND_EXTREME | h+24 | 156 | +0.46% | 0.015 |

## Tier T fade candidates (`p <= 0.05`, negative net)

| symbol | tf | event | h | n | net | p-value |
|---|---|---|---|---|---|---|
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+1 | 6620 | -0.17% | 0.007 |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+3 | 6620 | -0.17% | 0.001 |
| BTCUSDT | 5m | VOL_BREAKOUT | h+1 | 1538 | -0.17% | 0.003 |
| BTCUSDT | 5m | FUND_EXTREME | h+3 | 156 | -0.13% | 0.014 |

## Tier M fade candidates (`p <= 0.10`, negative net)

| symbol | tf | event | h | n | net | p-value |
|---|---|---|---|---|---|---|
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+1 | 6620 | -0.09% | 0.007 |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+3 | 6620 | -0.09% | 0.001 |
| BTCUSDT | 5m | VOL_BREAKOUT | h+1 | 1538 | -0.09% | 0.003 |
| BTCUSDT | 5m | FUND_EXTREME | h+3 | 156 | -0.05% | 0.014 |

