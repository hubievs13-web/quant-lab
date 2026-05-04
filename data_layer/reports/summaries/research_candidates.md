# Research Candidates

Last refresh: 2026-05-04 15:23 UTC.
Cells that pass every stability gate at once. Tier T uses `p <= 0.05`; Tier M uses `p <= 0.10` (relaxed while only 365 days of data are available). All rows already require `n >= 80` and walk-forward sign stability for the matching tier. **Long sections** list cells with a stable positive net; trade in the direction implied by the event. **Fade sections** list cells with a stable *negative* net; the hypothesis must declare `direction: fade` and trade against the event. Source: `walk_forward.md` + `permutation_test.md`.

## Cross-symbol Pareto + stability (highest grade)

None at the current window. The auditor cross-symbol Pareto gate is currently empty for every tier and direction.

## Tier T long candidates (`p <= 0.05`)

None.

## Tier M long candidates (`p <= 0.10`)

None.

## Tier T fade candidates (`p <= 0.05`, negative net)

| symbol | tf | event | h | n | net | p-value |
|---|---|---|---|---|---|---|
| BTCUSDT | 5m | VOL_BREAKOUT | h+72 | 512 | -0.32% | 0.006 |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+1 | 2224 | -0.17% | 0.017 |

## Tier M fade candidates (`p <= 0.10`, negative net)

| symbol | tf | event | h | n | net | p-value |
|---|---|---|---|---|---|---|
| BTCUSDT | 5m | VOL_BREAKOUT | h+72 | 512 | -0.24% | 0.006 |
| BTCUSDT | 5m | VOL_BREAKOUT | h+12 | 512 | -0.13% | 0.081 |
| BTCUSDT | 5m | PREMIUM_COMPRESSION | h+1 | 2224 | -0.09% | 0.017 |
| ETHUSDT | 5m | VOL_BREAKOUT | h+1 | 587 | -0.08% | 0.078 |
| BTCUSDT | 1h | PREMIUM_SPIKE | h+1 | 256 | -0.05% | 0.070 |

