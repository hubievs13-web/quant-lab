# Data Layer Ingest Log

Append-only log of Data Layer fetch / refresh runs. Newest entries
go at the bottom. Format:

    <YYYY-MM-DD> | <source> | <status> | <notes>

Do not edit prior lines.

## Entries

2026-05-03 | binance.ohlcv (BTCUSDT, 5m, 7d)            | success | rows=2016 files=7
2026-05-03 | binance.ohlcv (BTCUSDT, 1h, 30d)           | success | rows=720 files=30
2026-05-03 | binance.funding (BTCUSDT, monthly 2026-04) | success | rows=90  months=1
2026-05-03 | binance.metrics/oi (BTCUSDT, 5m, 7d)       | success | rows=2016 files=7
2026-05-03 | rebuild align+join (BTCUSDT 5m, 1h)        | success | bars=2016 + 720
2026-05-03 | quality smoke (BTCUSDT)                    | green   | dups=0 ooo=0 oi_gap_max=5.0min
