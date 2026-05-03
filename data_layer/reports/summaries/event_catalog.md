# Event Catalog

Last refresh: 2026-05-03 13:39 UTC.
Source: `data_layer/store/processed/events/binance/<SYMBOL>/<TF>.parquet`.
Defs in `data_layer/config/events.yaml` and `data_layer/process/events.py:THRESH`.

Anti-lookahead: each event uses only features at bar i; first-cross only (False -> True transition).

## Implemented events (binance, BTCUSDT)

| event_type | description | 5m count | 1h count |
|---|---|---|---|
| EV_FUND_FLIP | funding_rate sign change between consecutive bars (>= 0.5 bp move) | 46 | 75 |
| EV_FUND_EXTREME | |funding_rate_zscore_30d| >= 2 (or |rate| >= 5 bp fallback) | 7 | 23 |
| EV_OI_SPIKE_UP | oi_pct_change_1h > +3% AND (oi_zscore_30d > 1 OR z insufficient) | 7 | 3 |
| EV_OI_FLUSH | oi_pct_change_1h < -3% | 3 | 0 |
| EV_VOL_BREAKOUT | range_pct >= rolling 99-pctile AND taker_quote_zscore_24 > 2 | 88 | 34 |
| EV_FUNDING_WINDOW_PRE | informational; minutes_to_next_settle <= 30 (first cross) | 264 | 175 |
| EV_PREMIUM_SPIKE | basis_zscore_24 >= +2 (mark - index spread spikes positive) | 735 | 131 |
| EV_PREMIUM_COMPRESSION | basis_zscore_24 <= -2 (mark - index spread spikes negative) | 563 | 71 |

## Skipped events (insufficient_data)

| event_type | reason |
|---|---|
| EV_LIQ_LONG_CASCADE | no liquidations ingest in v1 |
| EV_LIQ_SHORT_CASCADE | no liquidations ingest in v1 |
| EV_CROWD_FLIP | LSR z-score requires >= 30 days of OI metrics history |

## Notes

- `event_strength` is in absolute z-score units where applicable; for fallback paths it is normalised to the same magnitude scale.
- `context_regime` on each event row is the `composite_label` from `processed/regimes` at the same `ts_open_ms`.
