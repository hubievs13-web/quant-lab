# Event Leaderboard

Last refresh: 2026-05-03 12:58 UTC.
Source: `data_layer/store/processed/leaderboard/binance/<SYMBOL>/<TF>.parquet`.
Ranking: top 12 (event_type, tf, horizon) cells by `sharpe_like`, requiring `count >= 3`.

| rank | event_type | tf | horizon | n | mean fwd | hit>0 | sharpe | MFE/|MAE| |
|---|---|---|---|---|---|---|---|---|
| 1 | EV_VOL_BREAKOUT | 1h | h+72 | 3 | +2.58% | 100% | 2.40 | 3.34 |
| 2 | EV_FUND_EXTREME | 1h | h+72 | 4 | +2.55% | 75% | 0.92 | 1.50 |
| 3 | EV_FUND_EXTREME | 1h | h+12 | 4 | -0.30% | 25% | -0.84 | 0.30 |
| 4 | EV_FUND_FLIP | 5m | h+72 | 5 | +0.21% | 60% | 0.65 | 2.04 |
| 5 | EV_FUND_FLIP | 5m | h+1 | 5 | -0.05% | 40% | -0.57 | 0.52 |
| 6 | EV_FUND_FLIP | 1h | h+3 | 12 | +0.26% | 67% | 0.47 | 2.07 |
| 7 | EV_FUND_FLIP | 5m | h+12 | 5 | +0.15% | 60% | 0.45 | 2.20 |
| 8 | EV_FUND_EXTREME | 1h | h+3 | 4 | -0.17% | 25% | -0.45 | 0.63 |
| 9 | EV_FUND_FLIP | 1h | h+1 | 12 | +0.08% | 67% | 0.44 | 0.87 |
| 10 | EV_FUNDING_WINDOW_PRE | 1h | h+72 | 26 | +1.12% | 58% | 0.43 | 1.41 |
| 11 | EV_FUND_FLIP | 1h | h+12 | 12 | +0.56% | 58% | 0.41 | 3.83 |
| 12 | EV_FUND_FLIP | 5m | h+3 | 5 | -0.05% | 40% | -0.33 | 1.03 |

## Caveats

- Smoke window is 7d (5m) / 30d (1h). Sample sizes are intentionally tiny.
- This is a descriptive scan, NOT a verdict. No hypothesis is generated.
- Direction split (long-side vs short-side) is Phase 5+; current view is long-side only.
