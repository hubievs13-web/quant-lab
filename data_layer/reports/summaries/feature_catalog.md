# Feature Catalog

Last refresh: 2026-05-03 17:51 UTC.
Source: `data_layer/store/processed/features/binance/<SYMBOL>/<TF>.parquet`.

Definitions below are shared by BTCUSDT and ETHUSDT on Binance.

| feature | description | window |
|---|---|---|
| ret_1 | close pct change over 1 bar | 1 bar |
| ret_3 | close pct change over 3 bars | 3 bars |
| ret_12 | close pct change over 12 bars | 12 bars |
| ret_72 | close pct change over 72 bars | 72 bars |
| vol_close_to_close_24 | rolling std of ret_1 over 24 bars | 24 bars |
| atr_14 | Wilder average true range over 14 bars | 14 bars |
| range_pct | (high-low)/close on the current closed bar | 1 bar |
| ema_fast_minus_slow_pct | (EMA(close,fast)-EMA(close,slow))/close, fast=12 slow=48 | fast=12 slow=48 bars |
| slope_ret_24 | OLS slope of log(close) over last 24 bars | 24 bars |
| vol_zscore_24 | z-score of ret_1 vs rolling 24-bar mean+std | 24 bars |
| taker_imbalance | (2*taker_buy_base - volume_base)/volume_base on closed bar | 1 bar |
| taker_quote_zscore_24 | z-score of taker_buy_quote vs rolling 24-bar mean+std | 24 bars |
| funding_rate_zscore_30d | z-score of funding_rate over rolling 30-day window; null until min_periods=7d met | 30 days |
| basis_bp | (mark_close - index_close)/index_close*1e4 on the closed bar; null when mark/index missing for the bar | 1 bar |
| basis_zscore_24 | z-score of basis_bp vs rolling 24-bar mean+std | 24 bars |
| oi_pct_change_1h | OI pct change over 1 hour | 1 hour |
| oi_pct_change_24h | OI pct change over 24 hours | 24 hours |
| oi_zscore_30d | z-score of OI over rolling 30-day window; null until min_periods=7d met | 30 days |
| pre_funding_30m | 1 if 0 < minutes_to_next_settle <= 30 else 0 | 1 bar |
| post_funding_30m | 1 if 0 <= minutes_since_last_settle <= 30 else 0 | 1 bar |
| funding_settle_bar | 1 if abs(minutes_to_next_settle) <= tf_min/2 else 0 | 1 bar |
| long_short_account_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source |
| top_trader_position_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source |
| taker_long_short_vol_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source |
