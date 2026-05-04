# Data Layer Quality Report (latest)

Generated: 2026-05-04 14:42 UTC
Source: Binance USD-M futures via `data.binance.vision` (public CDN).

## OHLCV (per series)

| symbol | tf | days | expected | received | dedup | missing | duplicates | out-of-order | status |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5m | 365 | 105120 | 105120 | 105120 | 0 | 0 | 0 | green |
| BTCUSDT | 1h | 365 | 8760 | 8760 | 8760 | 0 | 0 | 0 | green |
| ETHUSDT | 5m | 365 | 105120 | 105120 | 105120 | 0 | 0 | 0 | green |
| ETHUSDT | 1h | 365 | 8760 | 8760 | 8760 | 0 | 0 | 0 | green |

## Funding

| symbol | rows received | rows expected (~) | first settle (ms) | last settle (ms) |
|---|---|---|---|---|
| BTCUSDT | 1095 | 1095 | 1746057600000 | 1777564800000 |
| ETHUSDT | 1095 | 1095 | 1746057600000 | 1777564800000 |

## Mark / Index price klines

| symbol | series | mark rows | index rows |
|---|---|---|---|
| BTCUSDT | 5m | 105120 | 105120 |
| BTCUSDT | 1h | 8760 | 8760 |
| ETHUSDT | 5m | 105120 | 105120 |
| ETHUSDT | 1h | 8760 | 8760 |

## Open Interest (5-minute granularity)

| symbol | rows received | max gap (minutes) | first ts (ms) | last ts (ms) |
|---|---|---|---|---|
| BTCUSDT | 105117 | 20.0 | 1746317100000 | 1777852800000 |
| ETHUSDT | 105117 | 20.0 | 1746317100000 | 1777852800000 |

## Notes

- Source: documented public archive `data.binance.vision`.
- Live Binance fapi REST is geoblocked from many cloud regions; the CDN is the v1 fallback.
- Status thresholds: green if dedup_ratio>=0.99 and 0 duplicates and 0 out-of-order rows.
