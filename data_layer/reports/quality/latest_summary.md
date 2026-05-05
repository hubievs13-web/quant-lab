# Data Layer Quality Report (latest)

Generated: 2026-05-05 15:39 UTC
Source: Binance USD-M futures via `data.binance.vision` (public CDN).

## OHLCV (per series)

| symbol | tf | days | expected | received | dedup | missing | duplicates | out-of-order | status |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5m | 1095 | 315360 | 315360 | 315360 | 0 | 0 | 0 | green |
| BTCUSDT | 1h | 1095 | 26280 | 26280 | 26280 | 0 | 0 | 0 | green |
| ETHUSDT | 5m | 1095 | 315360 | 315360 | 315360 | 0 | 0 | 0 | green |
| ETHUSDT | 1h | 1095 | 26280 | 26280 | 26280 | 0 | 0 | 0 | green |

## Funding

| symbol | rows received | rows expected (~) | first settle (ms) | last settle (ms) |
|---|---|---|---|---|
| BTCUSDT | 3288 | 3285 | 1682899200004 | 1777564800000 |
| ETHUSDT | 3288 | 3285 | 1682899200004 | 1777564800000 |

## Mark / Index price klines

| symbol | series | mark rows | index rows |
|---|---|---|---|
| BTCUSDT | 5m | 315355 | 313916 |
| BTCUSDT | 1h | 26280 | 26160 |
| ETHUSDT | 5m | 315355 | 315068 |
| ETHUSDT | 1h | 26280 | 26256 |

## Open Interest (5-minute granularity)

| symbol | rows received | max gap (minutes) | first ts (ms) | last ts (ms) |
|---|---|---|---|---|
| BTCUSDT | 105117 | 20.0 | 1746317100000 | 1777852800000 |
| ETHUSDT | 105117 | 20.0 | 1746317100000 | 1777852800000 |

## Notes

- Source: documented public archive `data.binance.vision`.
- Live Binance fapi REST is geoblocked from many cloud regions; the CDN is the v1 fallback.
- Status thresholds: green if dedup_ratio>=0.99 and 0 duplicates and 0 out-of-order rows.
