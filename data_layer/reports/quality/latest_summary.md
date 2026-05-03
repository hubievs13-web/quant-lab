# Data Layer Quality Report (latest)

Generated: 2026-05-03 12:35 UTC
Source: Binance USD-M futures via `data.binance.vision` (public CDN).

## OHLCV (per series)

| symbol | tf | days | expected | received | dedup | missing | duplicates | out-of-order | status |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5m | 7 | 2016 | 2016 | 2016 | 0 | 0 | 0 | green |
| BTCUSDT | 1h | 30 | 720 | 720 | 720 | 0 | 0 | 0 | green |

## Funding

| symbol | rows received | rows expected (~) | first settle (ms) | last settle (ms) |
|---|---|---|---|---|
| BTCUSDT | 90 | 90 | 1775001600000 | 1777564800000 |

## Open Interest (5-minute granularity)

| symbol | rows received | max gap (minutes) | first ts (ms) | last ts (ms) |
|---|---|---|---|---|
| BTCUSDT | 2016 | 5.0 | 1777161900000 | 1777766400000 |

## Notes

- Source: documented public archive `data.binance.vision`.
- Live Binance fapi REST is geoblocked from many cloud regions; the CDN is the v1 fallback.
- Status thresholds: green if dedup_ratio>=0.99 and 0 duplicates and 0 out-of-order rows.
