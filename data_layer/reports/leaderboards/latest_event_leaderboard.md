# Event Leaderboard

Last refresh: 2026-05-03 13:39 UTC.
Source: `data_layer/store/processed/leaderboard/binance/<SYMBOL>/<TF>.parquet`.
Ranking: top 12 (event_type, tf, horizon) cells by `sharpe_like`, requiring `count >= 30`.

| rank | event_type | tf | horizon | n | mean fwd | hit>0 | sharpe | MFE/|MAE| |
|---|---|---|---|---|---|---|---|---|
| 1 | EV_VOL_BREAKOUT | 1h | h+3 | 34 | -0.54% | 32% | -0.39 | 0.45 |
| 2 | EV_VOL_BREAKOUT | 1h | h+1 | 34 | -0.25% | 35% | -0.26 | 0.71 |
| 3 | EV_VOL_BREAKOUT | 5m | h+1 | 88 | -0.08% | 47% | -0.21 | 0.72 |
| 4 | EV_PREMIUM_COMPRESSION | 1h | h+3 | 71 | +0.15% | 59% | 0.20 | 1.10 |
| 5 | EV_PREMIUM_SPIKE | 1h | h+3 | 131 | +0.16% | 58% | 0.16 | 1.50 |
| 6 | EV_VOL_BREAKOUT | 5m | h+3 | 88 | -0.07% | 47% | -0.14 | 0.96 |
| 7 | EV_FUND_FLIP | 1h | h+24 | 75 | +0.32% | 49% | 0.14 | 1.13 |
| 8 | EV_FUND_FLIP | 5m | h+12 | 46 | +0.07% | 54% | 0.13 | 1.11 |
| 9 | EV_PREMIUM_SPIKE | 1h | h+1 | 131 | +0.07% | 53% | 0.12 | 1.02 |
| 10 | EV_VOL_BREAKOUT | 5m | h+72 | 87 | +0.24% | 60% | 0.12 | 0.95 |
| 11 | EV_VOL_BREAKOUT | 1h | h+24 | 34 | +0.36% | 47% | 0.12 | 0.74 |
| 12 | EV_FUND_FLIP | 1h | h+1 | 75 | -0.06% | 52% | -0.11 | 0.83 |

## Caveats

- History window: 90d (5m) / 180d (1h); cells with n<30 are excluded from this ranking but still present in the leaderboard parquet.
- This is a descriptive scan, NOT a verdict. No hypothesis is generated.
- Direction split (long-side vs short-side) is Phase 5+; current view is long-side only.
