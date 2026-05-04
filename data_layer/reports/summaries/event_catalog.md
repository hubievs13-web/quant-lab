# Event Catalog

Last refresh: 2026-05-04 13:34 UTC.
Source: `data_layer/store/processed/events/binance/<SYMBOL>/<TF>.parquet`.

| event_type | 5m BTC | 5m ETH | 1h BTC | 1h ETH |
|---|---|---|---|---|
| EV_FUND_FLIP | 46 | 53 | 75 | 77 |
| EV_FUND_EXTREME | 7 | 10 | 22 | 20 |
| EV_OI_SPIKE_UP | 7 | 3 | 3 | 2 |
| EV_OI_FLUSH | 3 | 4 | 0 | 1 |
| EV_VOL_BREAKOUT | 81 | 98 | 34 | 39 |
| EV_FUNDING_WINDOW_PRE | 261 | 261 | 174 | 174 |
| EV_PREMIUM_SPIKE | 736 | 750 | 132 | 137 |
| EV_PREMIUM_COMPRESSION | 564 | 537 | 71 | 75 |

## Notes

- `EV_FUND_FLIP`: funding_rate sign change between consecutive bars (>= 0.5 bp move)
- `EV_FUND_EXTREME`: |funding_rate_zscore_30d| >= 2 (or |rate| >= 5 bp fallback)
- `EV_OI_SPIKE_UP`: oi_pct_change_1h > +3% AND (oi_zscore_30d > 1 OR z insufficient)
- `EV_OI_FLUSH`: oi_pct_change_1h < -3%
- `EV_VOL_BREAKOUT`: range_pct >= rolling 99-pctile AND taker_quote_zscore_24 > 2
- `EV_FUNDING_WINDOW_PRE`: informational; minutes_to_next_settle <= 30 (first cross)
- `EV_PREMIUM_SPIKE`: basis_zscore_24 >= +2 (mark - index spread spikes positive)
- `EV_PREMIUM_COMPRESSION`: basis_zscore_24 <= -2 (mark - index spread spikes negative)
- `EV_LIQ_LONG_CASCADE` skipped: no liquidations ingest in v1.
- `EV_LIQ_SHORT_CASCADE` skipped: no liquidations ingest in v1.
- `EV_CROWD_FLIP` skipped: LSR z-score requires >= 30 days of OI metrics history.
