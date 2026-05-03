# Event Leaderboard

Last refresh: 2026-05-03 13:12 UTC.
Source: `data_layer/store/processed/leaderboard/binance/<SYMBOL>/<TF>.parquet`.
Ranking: top 12 (event_type, tf, horizon) cells by `sharpe_like`, requiring `count >= 30`.

| rank | event_type | tf | horizon | n | mean fwd | hit>0 | sharpe | MFE/|MAE| |
|---|---|---|---|---|---|---|---|---|
| 1 | EV_VOL_BREAKOUT | 1h | h+3 | 34 | -0.54% | 32% | -0.39 | 0.45 |
| 2 | EV_VOL_BREAKOUT | 5m | h+72 | 48 | +0.51% | 69% | 0.37 | 1.30 |
| 3 | EV_VOL_BREAKOUT | 1h | h+1 | 34 | -0.25% | 35% | -0.26 | 0.71 |
| 4 | EV_PREMIUM_COMPRESSION | 1h | h+3 | 71 | +0.15% | 59% | 0.20 | 1.10 |
| 5 | EV_PREMIUM_SPIKE | 5m | h+72 | 241 | +0.20% | 61% | 0.19 | 1.36 |
| 6 | EV_FUNDING_WINDOW_PRE | 5m | h+12 | 84 | +0.05% | 55% | 0.19 | 1.39 |
| 7 | EV_PREMIUM_SPIKE | 1h | h+3 | 131 | +0.16% | 58% | 0.16 | 1.50 |
| 8 | EV_FUND_FLIP | 1h | h+24 | 75 | +0.32% | 49% | 0.14 | 1.13 |
| 9 | EV_VOL_BREAKOUT | 5m | h+1 | 49 | -0.02% | 43% | -0.13 | 0.69 |
| 10 | EV_PREMIUM_SPIKE | 1h | h+1 | 131 | +0.07% | 53% | 0.12 | 1.02 |
| 11 | EV_VOL_BREAKOUT | 1h | h+24 | 34 | +0.36% | 47% | 0.12 | 0.74 |
| 12 | EV_FUND_FLIP | 1h | h+1 | 75 | -0.06% | 52% | -0.11 | 0.83 |

## Caveats

- History window: 30d (5m) / 180d (1h); cells with n<30 are excluded from this ranking but still present in the leaderboard parquet.
- This is a descriptive scan, NOT a verdict. No hypothesis is generated.
- Direction split (long-side vs short-side) is Phase 5+; current view is long-side only.
