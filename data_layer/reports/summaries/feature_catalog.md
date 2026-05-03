# Feature Catalog

Last refresh: 2026-05-03 13:12 UTC.
Source: `data_layer/store/processed/features/binance/<SYMBOL>/<TF>.parquet`.
Defs in `data_layer/config/features.yaml` and `data_layer/process/features.py`.

Anti-lookahead: every feature for bar i uses only bar i and earlier.

## Features (binance, BTCUSDT)

| feature | description | window | 5m non-null | 1h non-null |
|---|---|---|---|---|
| ret_1 | close pct change over 1 bar | 1 bar | 8639/8640 | 4319/4320 |
| ret_3 | close pct change over 3 bars | 3 bars | 8637/8640 | 4317/4320 |
| ret_12 | close pct change over 12 bars | 12 bars | 8628/8640 | 4308/4320 |
| ret_72 | close pct change over 72 bars | 72 bars | 8568/8640 | 4248/4320 |
| vol_close_to_close_24 | rolling std of ret_1 over 24 bars | 24 bars | 8616/8640 | 4296/4320 |
| atr_14 | Wilder average true range over 14 bars | 14 bars | 8627/8640 | 4307/4320 |
| range_pct | (high-low)/close on the current closed bar | 1 bar | 8640/8640 | 4320/4320 |
| ema_fast_minus_slow_pct | (EMA(close,fast)-EMA(close,slow))/close, fast=12 slow=48 | fast=12 slow=48 bars | 8593/8640 | 4273/4320 |
| slope_ret_24 | OLS slope of log(close) over last 24 bars | 24 bars | 8617/8640 | 4297/4320 |
| vol_zscore_24 | z-score of ret_1 vs rolling 24-bar mean+std | 24 bars | 8616/8640 | 4296/4320 |
| taker_imbalance | (2*taker_buy_base - volume_base)/volume_base on closed bar | 1 bar | 8640/8640 | 4320/4320 |
| taker_quote_zscore_24 | z-score of taker_buy_quote vs rolling 24-bar mean+std | 24 bars | 8617/8640 | 4297/4320 |
| funding_rate_zscore_30d | z-score of funding_rate over rolling 30-day window; null until min_periods=7d met | 30 days | 6050/8640 | 4106/4320 |
| basis_bp | (mark_close - index_close)/index_close*1e4 on the closed bar; null when mark/index missing for the bar | 1 bar | 8640/8640 | 4320/4320 |
| basis_zscore_24 | z-score of basis_bp vs rolling 24-bar mean+std | 24 bars | 8617/8640 | 4297/4320 |
| oi_pct_change_1h | OI pct change over 1 hour | 1 hour | 8627/8640 | 718/4320 |
| oi_pct_change_24h | OI pct change over 24 hours | 24 hours | 8351/8640 | 695/4320 |
| oi_zscore_30d | z-score of OI over rolling 30-day window; null until min_periods=7d met | 30 days | 6624/8640 | 552/4320 |
| pre_funding_30m | 1 if 0 < minutes_to_next_settle <= 30 else 0 | 1 bar | 8640/8640 | 4320/4320 |
| post_funding_30m | 1 if 0 <= minutes_since_last_settle <= 30 else 0 | 1 bar | 8640/8640 | 4320/4320 |
| funding_settle_bar | 1 if abs(minutes_to_next_settle) <= tf_min/2 else 0 | 1 bar | 8640/8640 | 4320/4320 |
| long_short_account_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source | 8639/8640 | 719/4320 |
| top_trader_position_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source | 8639/8640 | 719/4320 |
| taker_long_short_vol_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source | 8639/8640 | 719/4320 |

## Insufficient_data notes

- `funding_rate_zscore_30d`, `oi_zscore_30d`: need >= 7 days of history before producing values; null on the warm-up tail of each window.
- `basis_bp` is computed from mark + index price klines fetched from data.binance.vision (futures/um daily archives).
- crowding cols come from raw OI metrics with 60-min TTL (asof backward).
