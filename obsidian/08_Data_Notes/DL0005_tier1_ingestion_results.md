---
id: DL0005
slug: tier1_ingestion_results
created: 2026-05-02
status: tier1_ingestion_partial
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0005 - tier1_ingestion_results

## 1. Ingestion Summary

Minimal Phase 2 TIER 1 ingestion was run for BTCUSDT and ETHUSDT only.

Created:

- `scripts/ingest_binance_um_tier1.py`
- `data/raw/binance_um/`
- `data/manifests/tier1_manifest.csv`
- `data/manifests/tier1_checksums.csv`
- `data/reports/tier1_gaps_report.csv`
- `data/reports/tier1_ingestion_errors.csv`

No H0008, strategy code, backtest, QuantConnect custom data, trading features, indicators, signals, parameter search, OI, taker statistics, basis endpoint data, liquidations, raw trades, or aggTrades were created.

Overall status: PARTIAL / STRICT INGESTION FAIL because 6 dataset-symbol-month files have missing rows. There were no failed HTTP requests.

## 2. Exact Date Range Ingested

- Start: `2024-01-01T00:00:00.000Z`
- End observed: `2026-05-02T07:19:00.000Z`
- Source mode: archive-first, with REST fallback used only for the newest not-yet-archived period.

## 3. Dataset-Symbol Status Table

| Dataset | Symbol | Rows | Non-OK months | Status |
|---|---:|---:|---:|---|
| `um_klines_1m` | BTCUSDT | 1,227,320 | 0 | OK |
| `um_klines_1m` | ETHUSDT | 1,227,320 | 0 | OK |
| `funding_rate_history` | BTCUSDT | 2,557 | 0 | OK |
| `funding_rate_history` | ETHUSDT | 2,557 | 0 | OK |
| `premium_index_klines` | BTCUSDT | 1,227,318 | 1 | INTEGRITY_FAIL |
| `premium_index_klines` | ETHUSDT | 1,227,318 | 1 | INTEGRITY_FAIL |
| `mark_price_klines` | BTCUSDT | 1,227,318 | 1 | INTEGRITY_FAIL |
| `mark_price_klines` | ETHUSDT | 1,227,318 | 1 | INTEGRITY_FAIL |
| `index_price_klines` | BTCUSDT | 1,227,318 | 1 | INTEGRITY_FAIL |
| `index_price_klines` | ETHUSDT | 1,227,318 | 1 | INTEGRITY_FAIL |

Manifest rows:

- Total: 290
- OK: 284
- INTEGRITY_FAIL: 6

## 4. Row Counts By Dataset And Symbol

See the table above. Total normalized raw files written: 290.

Compressed normalized raw size:

| Dataset | Files | Bytes |
|---|---:|---:|
| `um_klines_1m` | 58 | 114,382,610 |
| `funding_rate_history` | 58 | 49,675 |
| `premium_index_klines` | 58 | 51,139,608 |
| `mark_price_klines` | 58 | 61,039,771 |
| `index_price_klines` | 58 | 60,839,582 |

## 5. Gap Summary

Total missing rows reported: 12.

Affected windows:

| Dataset | Symbol | Window | Missing rows | Missing timestamps |
|---|---:|---|---:|---|
| `premium_index_klines` | BTCUSDT | 2024-08 | 2 | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |
| `premium_index_klines` | ETHUSDT | 2024-08 | 2 | same two timestamps |
| `mark_price_klines` | BTCUSDT | 2024-08 | 2 | same two timestamps |
| `mark_price_klines` | ETHUSDT | 2024-08 | 2 | same two timestamps |
| `index_price_klines` | BTCUSDT | 2024-08 | 2 | same two timestamps |
| `index_price_klines` | ETHUSDT | 2024-08 | 2 | same two timestamps |

No missing rows were reported for `um_klines_1m` or `funding_rate_history`.

## 6. Duplicate Summary

Duplicate rows: 0.

Timestamp monotonicity failures: 0.

## 7. Checksum Summary

Checksum rows written: 290.

All saved normalized files have non-empty SHA-256 checksums in `data/manifests/tier1_checksums.csv`.

Total compressed normalized bytes: 287,451,246.

## 8. Failed Requests / Errors

`data/reports/tier1_ingestion_errors.csv` contains 0 error rows.

The integrity failures are data gaps, not request failures.

## 9. Sufficiency For Future Researcher Cycle

Strictly, not sufficient yet.

The ingestion did not pass the required integrity gate because six price-state files have missing 1m rows. A future researcher cycle should not start until the project either resolves these missing rows from an approved source or explicitly accepts a gap policy that treats these two timestamps as no-data / no-signal rows without forward-fill or backfill.

## 10. Future Candidates Now Partially Enabled

These candidates are data-covered but not cleared for research until the integrity issue is resolved:

- premium compression repricing,
- mark-last dislocation,
- funding regime reversal with premium confirmation,
- derived basis using perp last price and index price.

## 11. Candidates Still Blocked

Still blocked:

- OI absorption,
- taker-flow imbalance,
- liquidation-based hypotheses.

Reasons:

- No historical OI ingestion was approved or performed.
- No taker buy/sell statistics, raw trades, or aggTrades were ingested.
- No liquidation data was ingested or approved.

## 12. Recommendation

Stop Phase 2 progression for now.

Do not proceed to point-in-time feature audit, H0008, strategy code, backtests, or QC custom data until the August 2024 price-state gaps are resolved or an explicit no-fill gap policy is approved for future research. Rerunning may not repair the issue if the official archive itself is missing those two minutes.
