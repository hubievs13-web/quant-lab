# Outcome Summary

Last refresh: 2026-05-03 12:58 UTC.
Source: `data_layer/store/processed/outcomes/binance/<SYMBOL>/<TF>.parquet`.
Anchor: bar AFTER event (next-bar entry; no same-bar contamination).
Counts are complete only; `inc` column lists rows where the horizon window was truncated by end-of-data.

## 5m (binance, BTCUSDT)

| event_type | h | n | inc | mean fwd | hit>0 | med MFE | med MAE |
|---|---|---|---|---|---|---|---|
| EV_FUNDING_WINDOW_PRE | h+1 | 16 | 0 | +0.01% | 44% | +0.03% | -0.06% |
| EV_FUNDING_WINDOW_PRE | h+3 | 16 | 0 | -0.01% | 62% | +0.08% | -0.10% |
| EV_FUNDING_WINDOW_PRE | h+12 | 16 | 0 | +0.00% | 44% | +0.17% | -0.16% |
| EV_FUNDING_WINDOW_PRE | h+72 | 16 | 0 | +0.04% | 44% | +0.61% | -0.40% |
| EV_FUND_FLIP | h+1 | 5 | 0 | -0.05% | 40% | +0.04% | -0.09% |
| EV_FUND_FLIP | h+3 | 5 | 0 | -0.05% | 40% | +0.10% | -0.09% |
| EV_FUND_FLIP | h+12 | 5 | 0 | +0.15% | 60% | +0.32% | -0.14% |
| EV_FUND_FLIP | h+72 | 5 | 0 | +0.21% | 60% | +0.62% | -0.30% |
| EV_OI_FLUSH | h+1 | 2 | 0 | +0.12% | 100% | +0.13% | -0.05% |
| EV_OI_FLUSH | h+3 | 2 | 0 | +0.05% | 50% | +0.18% | -0.05% |
| EV_OI_FLUSH | h+12 | 2 | 0 | -0.15% | 0% | +0.19% | -0.36% |
| EV_OI_FLUSH | h+72 | 2 | 0 | +0.11% | 100% | +0.34% | -0.36% |
| EV_OI_SPIKE_UP | h+1 | 1 | 0 | -0.29% | 0% | +0.13% | -0.32% |
| EV_OI_SPIKE_UP | h+3 | 1 | 0 | -0.12% | 0% | +0.13% | -0.41% |
| EV_OI_SPIKE_UP | h+12 | 1 | 0 | -0.25% | 0% | +0.62% | -0.41% |
| EV_OI_SPIKE_UP | h+72 | 1 | 0 | -0.11% | 0% | +0.62% | -0.50% |
| EV_VOL_BREAKOUT | h+1 | 8 | 0 | -0.02% | 25% | +0.10% | -0.13% |
| EV_VOL_BREAKOUT | h+3 | 8 | 0 | -0.05% | 25% | +0.18% | -0.14% |
| EV_VOL_BREAKOUT | h+12 | 8 | 0 | -0.00% | 38% | +0.28% | -0.29% |
| EV_VOL_BREAKOUT | h+72 | 7 | 1 | -0.15% | 57% | +0.29% | -0.45% |

## 1h (binance, BTCUSDT)

| event_type | h | n | inc | mean fwd | hit>0 | med MFE | med MAE |
|---|---|---|---|---|---|---|---|
| EV_FUNDING_WINDOW_PRE | h+1 | 27 | 0 | -0.09% | 37% | +0.16% | -0.23% |
| EV_FUNDING_WINDOW_PRE | h+3 | 27 | 0 | -0.02% | 44% | +0.31% | -0.49% |
| EV_FUNDING_WINDOW_PRE | h+12 | 27 | 0 | +0.05% | 41% | +0.91% | -0.95% |
| EV_FUNDING_WINDOW_PRE | h+24 | 27 | 0 | +0.06% | 44% | +1.26% | -1.48% |
| EV_FUNDING_WINDOW_PRE | h+72 | 26 | 1 | +1.12% | 58% | +3.06% | -2.18% |
| EV_FUND_EXTREME | h+1 | 4 | 0 | +0.04% | 75% | +0.31% | -0.16% |
| EV_FUND_EXTREME | h+3 | 4 | 0 | -0.17% | 25% | +0.31% | -0.49% |
| EV_FUND_EXTREME | h+12 | 4 | 0 | -0.30% | 25% | +0.31% | -1.04% |
| EV_FUND_EXTREME | h+24 | 4 | 0 | -0.37% | 50% | +1.16% | -1.86% |
| EV_FUND_EXTREME | h+72 | 4 | 0 | +2.55% | 75% | +3.84% | -2.57% |
| EV_FUND_FLIP | h+1 | 12 | 0 | +0.08% | 67% | +0.19% | -0.22% |
| EV_FUND_FLIP | h+3 | 12 | 0 | +0.26% | 67% | +0.52% | -0.25% |
| EV_FUND_FLIP | h+12 | 12 | 0 | +0.56% | 58% | +1.45% | -0.38% |
| EV_FUND_FLIP | h+24 | 12 | 0 | +0.42% | 58% | +1.93% | -0.76% |
| EV_FUND_FLIP | h+72 | 11 | 1 | +0.55% | 45% | +3.13% | -1.59% |
| EV_VOL_BREAKOUT | h+1 | 3 | 0 | +0.15% | 33% | +0.27% | -0.23% |
| EV_VOL_BREAKOUT | h+3 | 3 | 0 | -0.12% | 33% | +0.27% | -0.49% |
| EV_VOL_BREAKOUT | h+12 | 3 | 0 | -0.25% | 33% | +0.27% | -0.98% |
| EV_VOL_BREAKOUT | h+24 | 3 | 0 | +1.04% | 33% | +1.35% | -1.70% |
| EV_VOL_BREAKOUT | h+72 | 3 | 0 | +2.58% | 100% | +5.90% | -1.76% |

## Reading guide

- `mean fwd` = mean of `forward_return_pct` over complete outcomes.
- `hit>0` = share of complete outcomes with positive forward_return.
- Smoke samples are tiny; `n < 30` should be treated as descriptive only.
