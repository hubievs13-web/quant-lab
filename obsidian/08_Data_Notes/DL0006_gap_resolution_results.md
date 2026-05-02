---
id: DL0006
slug: gap_resolution_results
created: 2026-05-02
status: gap_resolution_partial
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0006 - gap_resolution_results

## 1. Gap-Resolution Summary

Phase 2 gap-resolution was attempted only for the exact August 2024 price-state gaps identified in DL0005.

Created:

- `scripts/resolve_tier1_price_state_gaps.py`
- `data/reports/tier1_gap_resolution_report.csv`

No H0008, strategy code, backtest, QuantConnect custom data, trading feature, signal, indicator, parameter search, OI, taker-statistics, basis endpoint data, liquidation data, raw trades, or aggTrades were created.

Binance REST requests completed with `OK` source status for all 12 target row checks, but the exact missing timestamps were not returned.

## 2. Exact Rows Targeted

Datasets:

- `premium_index_klines`
- `mark_price_klines`
- `index_price_klines`

Symbols:

- BTCUSDT
- ETHUSDT

Target timestamps:

- `2024-08-12T10:02:00.000Z`
- `2024-08-12T10:03:00.000Z`

REST query window:

- `startTime=2024-08-12T10:00:00Z`
- `endTime=2024-08-12T10:05:00Z`

## 3. Exact Rows Recovered

Recovered rows: 0.

Inserted rows: 0.

Report summary:

- Rows in `tier1_gap_resolution_report.csv`: 12
- `source_status=OK`: 12
- `recovered=FALSE`: 12
- `inserted=FALSE`: 12
- `validation_status=NOT_RETURNED`: 12

## 4. Exact Rows Still Missing

All 12 target rows remain missing:

| Dataset | Symbol | Missing timestamps |
|---|---:|---|
| `premium_index_klines` | BTCUSDT | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |
| `premium_index_klines` | ETHUSDT | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |
| `mark_price_klines` | BTCUSDT | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |
| `mark_price_klines` | ETHUSDT | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |
| `index_price_klines` | BTCUSDT | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |
| `index_price_klines` | ETHUSDT | `2024-08-12T10:02:00Z`, `2024-08-12T10:03:00Z` |

## 5. Files Modified

Normalized raw data files were not modified because no exact source rows were recovered.

Updated audit/report files:

- `data/reports/tier1_gap_resolution_report.csv`
- `data/manifests/tier1_manifest.csv`
- `data/reports/tier1_gaps_report.csv`
- `data/manifests/tier1_checksums.csv`

`data/reports/tier1_ingestion_errors.csv` remains at 0 error rows; no new request errors occurred.

No raw REST audit snippets were saved because no rows were recovered.

## 6. Updated Integrity Status

Updated integrity status: PARTIAL.

Current manifest status:

- OK rows: 284
- INTEGRITY_FAIL rows: 6

Current gaps status:

- Total missing rows: 12
- Duplicate rows: 0
- Non-monotonic timestamp rows: 0

No new integrity issue was introduced.

## 7. Point-In-Time Feature Audit Status

Point-in-time feature audit is not allowed yet under strict ingestion rules.

It can proceed only after an explicit project decision to accept a no-fill/no-signal gap policy, accept a reduced research date window excluding the affected timestamps/day, use approved vendor data, or stop Phase 2.

## 8. Recommendation

Recommended next decision: approve a no-fill/no-signal policy for these exact two timestamps, if the project accepts a 12-row known gap across price-state datasets.

Alternative options:

- accept a reduced research date window excluding `2024-08-12`,
- stop Phase 2,
- use paid/vendor data for an independent repair source.

Do not forward-fill, backfill, interpolate, synthesize, or infer these rows from neighboring values.

## 9. Files Changed

- `scripts/resolve_tier1_price_state_gaps.py`
- `data/reports/tier1_gap_resolution_report.csv`
- `data/manifests/tier1_manifest.csv`
- `data/reports/tier1_gaps_report.csv`
- `data/manifests/tier1_checksums.csv`
- `obsidian/08_Data_Notes/DL0006_gap_resolution_results.md`
