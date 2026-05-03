# Feature Catalog

Last refresh: 2026-05-03 12:48 UTC.
Source: `data_layer/store/processed/features/binance/<SYMBOL>/<TF>.parquet`.
Defs in `data_layer/config/features.yaml` and `data_layer/process/features.py`.

Anti-lookahead: every feature for bar i uses only bar i and earlier.

## Features (binance, BTCUSDT)

| feature | description | window | 5m non-null | 1h non-null |
|---|---|---|---|---|
| ret_1 | close pct change over 1 bar | 1 bar | 2015/2016 | 719/720 |
| ret_3 | close pct change over 3 bars | 3 bars | 2013/2016 | 717/720 |
| ret_12 | close pct change over 12 bars | 12 bars | 2004/2016 | 708/720 |
| ret_72 | close pct change over 72 bars | 72 bars | 1944/2016 | 648/720 |
| vol_close_to_close_24 | rolling std of ret_1 over 24 bars | 24 bars | 1992/2016 | 696/720 |
| atr_14 | Wilder average true range over 14 bars | 14 bars | 2003/2016 | 707/720 |
| range_pct | (high-low)/close on the current closed bar | 1 bar | 2016/2016 | 720/720 |
| ema_fast_minus_slow_pct | (EMA(close,fast)-EMA(close,slow))/close, fast=12 slow=48 | fast=12 slow=48 bars | 1969/2016 | 673/720 |
| slope_ret_24 | OLS slope of log(close) over last 24 bars | 24 bars | 1993/2016 | 697/720 |
| vol_zscore_24 | z-score of ret_1 vs rolling 24-bar mean+std | 24 bars | 1992/2016 | 696/720 |
| taker_imbalance | (2*taker_buy_base - volume_base)/volume_base on closed bar | 1 bar | 2016/2016 | 720/720 |
| taker_quote_zscore_24 | z-score of taker_buy_quote vs rolling 24-bar mean+std | 24 bars | 1993/2016 | 697/720 |
| funding_rate_zscore_30d | z-score of funding_rate over rolling 30-day window; null until min_periods=7d met | 30 days | 0/2016 | 506/720 |
| basis_bp | (mark-index)/index*1e4; insufficient_data in Phase 2/3 (no mark/index series ingested yet) | 1 bar | 0/2016 | 0/720 |
| oi_pct_change_1h | OI pct change over 1 hour | 1 hour | 2003/2016 | 166/720 |
| oi_pct_change_24h | OI pct change over 24 hours | 24 hours | 1727/2016 | 143/720 |
| oi_zscore_30d | z-score of OI over rolling 30-day window; null until min_periods=7d met | 30 days | 0/2016 | 0/720 |
| pre_funding_30m | 1 if 0 < minutes_to_next_settle <= 30 else 0 | 1 bar | 2016/2016 | 720/720 |
| post_funding_30m | 1 if 0 <= minutes_since_last_settle <= 30 else 0 | 1 bar | 2016/2016 | 720/720 |
| funding_settle_bar | 1 if abs(minutes_to_next_settle) <= tf_min/2 else 0 | 1 bar | 2016/2016 | 720/720 |
| long_short_account_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source | 2015/2016 | 167/720 |
| top_trader_position_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source | 2015/2016 | 167/720 |
| taker_long_short_vol_ratio | joined from raw daily metrics (asof, 60min TTL) | 5 min source | 2015/2016 | 167/720 |

## Insufficient_data notes

- `funding_rate_zscore_30d`, `oi_zscore_30d`: require >= 7 days of history; smoke 5m window is 7 days (still sparse), so 5m yields 0 valid.
- `basis_bp`: mark/index series not ingested in Phase 2/3; populated in Phase 4+.
- crowding cols come from raw OI metrics with 60-min TTL (asof backward).
