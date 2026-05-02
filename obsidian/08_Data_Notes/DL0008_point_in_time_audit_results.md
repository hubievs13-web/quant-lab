---
id: DL0008
slug: point_in_time_audit_results
created: 2026-05-02
status: point_in_time_audit_pass
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0008 - point_in_time_audit_results

## 1. Audit Summary

Point-in-time audit was run for the accepted Phase 2 TIER 1 datasets with the DL0007 no-fill/no-signal exception.

Created:

- `scripts/audit_point_in_time_tier1.py`
- `data/reports/point_in_time_audit_summary.csv`
- `data/reports/point_in_time_availability_flags.csv`
- `data/reports/point_in_time_5m_dependency_audit.csv`
- `data/reports/point_in_time_audit_errors.csv`

No H0008, strategy code, backtest, QuantConnect custom data, trading signals, entry/exit rules, indicators, parameter search, OI, taker statistics, basis endpoint data, liquidations, raw trades, or aggTrades were created.

Overall audit status: PASS.

Summary:

- Audit summary rows: 34
- PASS checks: 34
- Failed checks: 0
- Audit errors: 0
- Availability rows: 2,454,640
- 5m dependency rows: 490,928

## 2. Dataset-Symbol Pass/Fail Table

| Dataset / check group | BTCUSDT | ETHUSDT | Notes |
|---|---|---|---|
| `um_klines_1m` source timestamps and completed 1m bars | PASS | PASS | 1,227,320 rows per symbol checked. |
| `premium_index_klines` source timestamps and completed 1m bars | PASS | PASS | 1,227,318 rows per symbol checked. |
| `mark_price_klines` source timestamps and completed 1m bars | PASS | PASS | 1,227,318 rows per symbol checked. |
| `index_price_klines` source timestamps and completed 1m bars | PASS | PASS | 1,227,318 rows per symbol checked. |
| `funding_rate_history` timestamp availability | PASS | PASS | 2,557 rows per symbol checked. |
| Price-state alignment vs perp klines | PASS | PASS | Only DL0007-approved gaps are missing. |
| DL0007 availability/no-signal flags | PASS | PASS | Exact missing timestamps remain unavailable and no-signal. |
| 5m dependency audit | PASS | PASS | Affected 5m bar is flagged no-signal. |
| No future transform / no OOS normalization | PASS | PASS | Audit created only boolean availability/count flags. |

## 3. DL0007 Gap Policy Verification

DL0007 gap timestamps remain missing and were not filled:

- `2024-08-12T10:02:00.000Z`
- `2024-08-12T10:03:00.000Z`

For both BTCUSDT and ETHUSDT, `point_in_time_availability_flags.csv` marks these minute rows as:

- `has_um_klines=TRUE`
- `has_premium_index=FALSE`
- `has_mark_price=FALSE`
- `has_index_price=FALSE`
- `has_all_price_state=FALSE`
- `dl0007_gap_timestamp=TRUE`
- `no_signal_required=TRUE`

No synthesis, interpolation, forward-fill, backfill, or inference was performed.

## 4. Funding Timestamp Availability Verification

Funding rows have valid source timestamps and are checked as available only at or after their own `timestamp_utc`.

The audit did not create funding-derived trading features. It created only an audit availability flag that advances when `funding_timestamp <= audit_timestamp`.

No final funding value is used before its funding timestamp in the audit transform.

## 5. 1m Source Alignment Verification

Premium, mark, and index price timestamps align with `um_klines_1m` except for the exact DL0007-approved gaps.

Per symbol and per price-state dataset:

- `missing_vs_um=2`
- `expected_dl0007_missing=2`
- `unexpected_extra=0`

No unexpected price-state timestamp gaps were found.

## 6. 5m Dependency / No-Signal Verification

For the 5m bar starting `2024-08-12T10:00:00.000Z`, both symbols have:

- required 1m rows: 5
- available `um_klines_1m` rows: 5
- available premium rows: 3
- available mark rows: 3
- available index rows: 3
- `complete_for_price_state_features=FALSE`
- `no_signal_required=TRUE`

This satisfies DL0007 for any future 5m feature that requires complete 1m price-state source data.

## 7. Failures Or Unresolved Leakage Risks

No audit failures were found.

Residual controls that must remain active in future work:

- Do not fill DL0007 missing rows.
- Propagate unavailable/no-signal flags into any future feature table.
- Use funding values only after their funding timestamp.
- If building 5m features, exclude dependent 5m bars when complete 1m source data is required.
- Do not introduce future-normalized transforms, labels, parameter search, or OOS influence during future researcher work.

## 8. Readiness For Researcher Cycle

Data is ready for a researcher cycle using only audited TIER 1 data and the DL0007 no-fill/no-signal exception.

H0008 is still not created. A researcher cycle must still evaluate mechanism distinctness, data availability, and the 0.10 percent pre-fee edge floor before any hypothesis is created.

## 9. Candidate Families Now Eligible To Consider

The next researcher cycle may consider only audited TIER 1 mechanisms such as:

- premium compression repricing,
- mark-last dislocation,
- funding regime reversal with premium confirmation,
- derived basis using perp last price and index price.

## 10. Candidate Families Still Blocked

Still blocked:

- OI absorption,
- taker-flow imbalance,
- liquidation-based hypotheses.

Reasons:

- No historical OI data was ingested.
- No taker buy/sell statistics, raw trades, or aggTrades were ingested.
- No liquidation data was ingested or approved.

## 11. Recommendation

Proceed to a researcher cycle using only audited TIER 1 data.

Do not create strategy code, run backtests, create QuantConnect custom data, or perform parameter search during the researcher cycle. H0008 should be created only if a candidate passes the usual mechanism and falsification-readiness checks.
