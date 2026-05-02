---
id: DL0007
slug: no_fill_no_signal_gap_policy
created: 2026-05-02
status: approved_policy
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0007 - no_fill_no_signal_gap_policy

## 1. Policy Summary

This note formally approves a no-fill/no-signal policy only for the exact unresolved TIER 1 price-state gaps identified in DL0005 and confirmed unresolved in DL0006.

No H0008 was created. No strategy code, backtest, QuantConnect custom data, trading features, signals, indicators, or parameter search are authorized by this note.

## 2. Exact Approved Gap Scope

Affected datasets:

- `premium_index_klines`
- `mark_price_klines`
- `index_price_klines`

Affected symbols:

- BTCUSDT
- ETHUSDT

Affected source timestamps:

- `2024-08-12T10:02:00Z`
- `2024-08-12T10:03:00Z`

This policy does not approve any other missing timestamp, symbol, dataset, or date range.

## 3. No-Fill Rule

No rows may be synthesized, interpolated, forward-filled, backfilled, inferred from neighboring data, or reconstructed from future data.

The missing rows remain missing. They must be treated as unavailable source observations.

## 4. No-Signal Rule

The exact affected timestamps must be treated as missing/no-signal rows in any future research artifact.

Any future feature table using these datasets must explicitly mark these timestamps as unavailable.

Any strategy or research process using these datasets must skip signal generation at these timestamps.

If a 5m or higher-timeframe feature/bar depends on complete 1m source data, then the dependent 5m bar must also be treated as unavailable/no-signal unless a later approved audit proves the feature does not require those missing source rows.

## 5. Point-In-Time Audit Gate

Point-in-time feature audit may proceed only after this policy is recorded.

The audit must verify that:

- missing source rows are not filled,
- unavailable timestamps are propagated into feature availability flags,
- signal generation is disabled where source completeness is required,
- no future values are used to compensate for the missing timestamps.

## 6. H0008 Status

H0008 remains not created.

This policy allows the next Phase 2 step to be a point-in-time feature audit request. It does not authorize hypothesis creation, strategy implementation, backtesting, QuantConnect custom data, or trading feature production.

## 7. Current Decision

TIER 1 ingestion is accepted with a known no-fill/no-signal exception for the exact 12 missing price-state observations listed above.

Future work must keep this exception visible in manifests, gap reports, feature audits, and any later researcher note that uses these datasets.
