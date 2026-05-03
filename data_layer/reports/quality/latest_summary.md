# Data Layer Quality Report (latest)

Generated: 2026-05-03 17:50 UTC
Source: Binance USD-M futures via `data.binance.vision` (public CDN).

## OHLCV (per series)

| symbol | tf | days | expected | received | dedup | missing | duplicates | out-of-order | status |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5m | 90 | 25920 | 0 | 0 | 25920 | 0 | 0 | red |
| BTCUSDT | 1h | 180 | 4320 | 0 | 0 | 4320 | 0 | 0 | red |
| ETHUSDT | 5m | 90 | 25920 | 25920 | 25920 | 0 | 0 | 0 | green |
| ETHUSDT | 1h | 180 | 4320 | 4320 | 4320 | 0 | 0 | 0 | green |

## Funding

| symbol | rows received | rows expected (~) | first settle (ms) | last settle (ms) |
|---|---|---|---|---|
| BTCUSDT | 0 | 540 | None | None |
| ETHUSDT | 543 | 540 | 1761955200001 | 1777564800000 |

## Mark / Index price klines

| symbol | series | mark rows | index rows |
|---|---|---|---|
| BTCUSDT | 5m | 0 | 0 |
| BTCUSDT | 1h | 0 | 0 |
| ETHUSDT | 5m | 25920 | 25920 |
| ETHUSDT | 1h | 4320 | 4320 |

## Open Interest (5-minute granularity)

| symbol | rows received | max gap (minutes) | first ts (ms) | last ts (ms) |
|---|---|---|---|---|
| BTCUSDT | 0 | - | None | None |
| ETHUSDT | 8640 | 5.0 | 1775174700000 | 1777766400000 |

## Notes

- Source: documented public archive `data.binance.vision`.
- Live Binance fapi REST is geoblocked from many cloud regions; the CDN is the v1 fallback.
- Status thresholds: green if dedup_ratio>=0.99 and 0 duplicates and 0 out-of-order rows.
