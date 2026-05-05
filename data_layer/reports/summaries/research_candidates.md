# Research Candidates

Last refresh: 2026-05-05 16:09 UTC.
Cells that pass every stability gate at once. Tier T uses `p <= 0.05`; Tier M uses `p <= 0.10` (kept slightly looser because maker friction is lower). All rows already require `n >= 80` and walk-forward sign stability for the matching tier. **Long sections** list cells with `mean_forward_return > friction` (the long trade clears fees by itself); the displayed `net` is the long-direction net after the matching tier's friction. **Fade sections** list cells with `mean_forward_return < -friction` (the unconditional return is reliably negative *enough* that flipping the sign and paying friction again still leaves a positive per-trade edge); the displayed `net` is the fade-direction net (i.e. `-mean_forward_return - friction`). Cells with small negative `full_net` but `|mean| < friction` are *not* fade-tradable and do not appear. Source: `walk_forward.md` + `permutation_test.md`.

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

## Tier T fade candidates (`p <= 0.05`, fade net after taker friction)

None.

## Tier M fade candidates (`p <= 0.10`, fade net after maker friction)

None.

