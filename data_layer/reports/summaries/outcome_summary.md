# Outcome Summary

Last refresh: 2026-05-03 13:12 UTC.
Source: `data_layer/store/processed/outcomes/binance/<SYMBOL>/<TF>.parquet`.
Anchor: bar AFTER event (next-bar entry; no same-bar contamination).
Counts are complete only. Rows with n < 10 omitted to keep the report compact; full table is in the leaderboard parquet.

## 5m (binance, BTCUSDT)

| event | h | n | fwd | hit | MFE | MAE |
|---|---|---|---|---|---|---|
| FUNDING_WINDOW_PRE | h+1 | 84 | +0.00% | 49% | +0.05% | -0.05% |
| FUNDING_WINDOW_PRE | h+3 | 84 | +0.01% | 61% | +0.09% | -0.08% |
| FUNDING_WINDOW_PRE | h+12 | 84 | +0.05% | 55% | +0.22% | -0.16% |
| FUNDING_WINDOW_PRE | h+72 | 84 | +0.08% | 51% | +0.65% | -0.39% |
| FUND_FLIP | h+1 | 12 | -0.01% | 50% | +0.05% | -0.07% |
| FUND_FLIP | h+3 | 12 | -0.02% | 50% | +0.11% | -0.10% |
| FUND_FLIP | h+12 | 12 | +0.04% | 50% | +0.32% | -0.16% |
| FUND_FLIP | h+72 | 12 | +0.10% | 50% | +0.68% | -0.50% |
| PREMIUM_COMPRESSION | h+1 | 194 | +0.00% | 54% | +0.05% | -0.04% |
| PREMIUM_COMPRESSION | h+3 | 194 | +0.02% | 55% | +0.12% | -0.08% |
| PREMIUM_COMPRESSION | h+12 | 194 | -0.01% | 47% | +0.22% | -0.23% |
| PREMIUM_COMPRESSION | h+72 | 193 | +0.06% | 51% | +0.59% | -0.54% |
| PREMIUM_SPIKE | h+1 | 244 | -0.01% | 48% | +0.05% | -0.06% |
| PREMIUM_SPIKE | h+3 | 244 | -0.01% | 43% | +0.09% | -0.11% |
| PREMIUM_SPIKE | h+12 | 244 | +0.04% | 54% | +0.23% | -0.22% |
| PREMIUM_SPIKE | h+72 | 241 | +0.20% | 61% | +0.65% | -0.48% |
| VOL_BREAKOUT | h+1 | 49 | -0.02% | 43% | +0.09% | -0.14% |
| VOL_BREAKOUT | h+3 | 49 | +0.01% | 53% | +0.24% | -0.20% |
| VOL_BREAKOUT | h+12 | 49 | +0.02% | 47% | +0.42% | -0.34% |
| VOL_BREAKOUT | h+72 | 48 | +0.51% | 69% | +0.75% | -0.58% |

## 1h (binance, BTCUSDT)

| event | h | n | fwd | hit | MFE | MAE |
|---|---|---|---|---|---|---|
| FUNDING_WINDOW_PRE | h+1 | 175 | -0.02% | 45% | +0.20% | -0.23% |
| FUNDING_WINDOW_PRE | h+3 | 175 | -0.06% | 43% | +0.33% | -0.45% |
| FUNDING_WINDOW_PRE | h+12 | 175 | -0.13% | 43% | +0.71% | -1.06% |
| FUNDING_WINDOW_PRE | h+24 | 175 | -0.19% | 44% | +1.24% | -1.75% |
| FUNDING_WINDOW_PRE | h+72 | 174 | +0.02% | 51% | +2.48% | -2.44% |
| FUND_EXTREME | h+1 | 23 | -0.12% | 43% | +0.24% | -0.29% |
| FUND_EXTREME | h+3 | 23 | -0.18% | 39% | +0.32% | -0.50% |
| FUND_EXTREME | h+12 | 23 | -0.10% | 39% | +0.71% | -1.22% |
| FUND_EXTREME | h+24 | 23 | +0.07% | 43% | +1.15% | -1.59% |
| FUND_EXTREME | h+72 | 23 | +0.90% | 61% | +3.92% | -1.85% |
| FUND_FLIP | h+1 | 75 | -0.06% | 52% | +0.22% | -0.27% |
| FUND_FLIP | h+3 | 75 | -0.05% | 48% | +0.39% | -0.39% |
| FUND_FLIP | h+12 | 75 | +0.02% | 48% | +1.00% | -1.07% |
| FUND_FLIP | h+24 | 75 | +0.32% | 49% | +1.73% | -1.53% |
| FUND_FLIP | h+72 | 74 | +0.12% | 51% | +2.81% | -2.06% |
| PREMIUM_COMPRESSION | h+1 | 71 | +0.01% | 49% | +0.27% | -0.32% |
| PREMIUM_COMPRESSION | h+3 | 71 | +0.15% | 59% | +0.49% | -0.45% |
| PREMIUM_COMPRESSION | h+12 | 71 | +0.19% | 45% | +0.81% | -0.94% |
| PREMIUM_COMPRESSION | h+24 | 71 | +0.11% | 48% | +1.15% | -1.44% |
| PREMIUM_COMPRESSION | h+72 | 69 | -0.00% | 51% | +2.47% | -2.63% |
| PREMIUM_SPIKE | h+1 | 131 | +0.07% | 53% | +0.31% | -0.30% |
| PREMIUM_SPIKE | h+3 | 131 | +0.16% | 58% | +0.68% | -0.45% |
| PREMIUM_SPIKE | h+12 | 131 | +0.12% | 55% | +1.18% | -0.87% |
| PREMIUM_SPIKE | h+24 | 131 | +0.22% | 53% | +1.69% | -1.35% |
| PREMIUM_SPIKE | h+72 | 131 | +0.08% | 54% | +3.04% | -2.16% |
| VOL_BREAKOUT | h+1 | 34 | -0.25% | 35% | +0.48% | -0.68% |
| VOL_BREAKOUT | h+3 | 34 | -0.54% | 32% | +0.51% | -1.12% |
| VOL_BREAKOUT | h+12 | 34 | +0.00% | 50% | +0.99% | -1.72% |
| VOL_BREAKOUT | h+24 | 34 | +0.36% | 47% | +1.61% | -2.16% |
| VOL_BREAKOUT | h+72 | 34 | +0.23% | 56% | +3.05% | -3.73% |

## Reading guide

- `mean fwd` = mean of `forward_return_pct` over complete outcomes.
- `hit>0` = share of complete outcomes with positive forward_return.
- Smoke samples are tiny; `n < 30` should be treated as descriptive only.
