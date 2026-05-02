---
id: DL0004
slug: archive_first_inventory_results
created: 2026-05-02
status: archive_first_inventory_result
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0004 - archive_first_inventory_results

## 1. Why DL0003 Was Inconclusive

DL0003 used a broader REST-heavy verifier and many Binance requests failed with SSL handshake timeouts. Only `index_price_klines` was cleanly verified as TIER 1 for both BTCUSDT and ETHUSDT. Other likely-free datasets remained UNKNOWN because the prior run did not get consistent old, 2024, recent, and schema evidence for both symbols.

DL0004 reran a narrower archive-first verification for likely TIER 1 datasets only:

1. `um_klines_1m`
2. `funding_rate_history`
3. `premium_index_klines`
4. `mark_price_klines`
5. `index_price_klines`

No OI, taker buy/sell, basis, liquidation, strategy, backtest, feature engineering, parameter search, QuantConnect custom data, or H0008 was created.

## 2. Final Dataset Table

| Dataset | BTCUSDT evidence | ETHUSDT evidence | Final tier | Approved for later minimal ingestion |
|---|---|---|---|---|
| `um_klines_1m` | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | TIER 1 | YES |
| `funding_rate_history` | 2021-01 archive OK, 2024-01 archive OK, latest archive OK, REST windows OK, 94 sample rows observed. | 2021-01 archive OK, 2024-01 archive OK, latest archive OK, REST windows OK, 94 sample rows observed. | TIER 1 | YES |
| `premium_index_klines` | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | TIER 1 | YES |
| `mark_price_klines` | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | TIER 1 | YES |
| `index_price_klines` | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | 2021-01 archive OK, 2024-01 archive OK, 2024 sample 500 rows OK, latest REST fallback OK. Latest completed-month archive was NOT_FOUND. | TIER 1 | YES |

## 3. Exact Tier Classification

TIER 1:

- `um_klines_1m`
- `funding_rate_history`
- `premium_index_klines`
- `mark_price_klines`
- `index_price_klines`

UNKNOWN:

- None among the five target datasets in this rerun.

TIER 2 / TIER 3 / TIER 4:

- Not checked in DL0004. DL0003 still applies for OI, taker buy/sell volume, and basis: OI/basis are recent-only class from Binance REST; taker buy/sell remains expected recent-only but was not cleanly verified. Historical liquidation data remains out of scope.

## 4. Approved For Later Minimal Ingestion

Approved to request a later minimal TIER 1 ingestion task:

- BTCUSDT and ETHUSDT only.
- Date range: 2024-01-01 to present first.
- Datasets: `um_klines_1m`, `funding_rate_history`, `premium_index_klines`, `mark_price_klines`, `index_price_klines`.
- Required outputs in that later task: manifest, checksums, gaps report.
- Still no backtest, H0008, feature engineering, parameter search, or QC custom data unless separately approved.

Important caveat: latest completed-month archive URLs for kline-like datasets returned NOT_FOUND for this run, probably because the latest monthly archive was not posted yet. Current coverage was verified with latest REST fallback. A later ingestion task should combine monthly archives for completed posted months with REST fallback for the most recent not-yet-archived period.

## 5. Blocked Or Still Unknown

Still blocked for immediate 12-month free research:

- Historical open interest statistics from Binance REST.
- Historical taker buy/sell volume statistics from Binance REST.
- Exchange basis endpoint history beyond recent windows.
- Historical liquidations.

These require paid vendor data, forward collection, or a separately approved raw-trade reconstruction plan.

## 6. Can Free-Only Phase 2 Support A Future Researcher Cycle?

Yes, but only for funding / premium / mark-index / derived-basis mechanisms that can be built from the verified TIER 1 datasets.

Examples potentially enabled after actual ingestion and gap validation:

- Premium compression repricing.
- Mark-last dislocation trigger pressure.
- Funding regime reversal with premium confirmation.
- Derived basis dislocation using perp last price and index price.

Not enabled by DL0004:

- OI absorption reversal.
- Taker-flow imbalance aftershock from Binance taker statistics.
- Liquidation-cascade hypotheses.

## 7. H0008 Status

H0008 is still not created.

The data inventory now supports requesting minimal TIER 1 ingestion, but a trading hypothesis should wait until actual data is ingested, gaps are audited, point-in-time alignment is confirmed, and candidate mechanisms are re-evaluated against the 0.10 percent pre-fee edge floor and distinct-from-rejected rules.

## 8. Files Created

- `scripts/verify_binance_um_archive_first.py`
- `data_inventory/source_inventory_archive_first.csv`
- `data_inventory/gaps_report_archive_first.csv`
- `data_inventory/checksums_archive_first.csv`
- `obsidian/08_Data_Notes/DL0004_archive_first_inventory_results.md`

Existing DL0003 outputs were not overwritten:

- `data_inventory/source_inventory.csv`
- `data_inventory/gaps_report.csv`
- `data_inventory/checksums.csv`

No `data/` folder was created. No full historical range was downloaded.

## 9. Errors And Timeouts

Final archive-first results:

- `archive_head_2021_01`: OK for all 10 dataset-symbol checks.
- `archive_head_2024_01`: OK for all 10 dataset-symbol checks.
- `archive_sample_get_2024_01`: OK for all 10 dataset-symbol checks.
- `checksum_get_2021_01`: OK for all 10 dataset-symbol checks.
- `checksum_get_2024_01`: OK for all 10 dataset-symbol checks.
- `rest_fallback_latest`: OK for all 10 dataset-symbol checks.
- `archive_head_latest`: NOT_FOUND for 8 kline-like checks and OK for 2 funding checks.

The NOT_FOUND latest archive result does not block TIER 1 classification because 2021-01 and 2024-01 archives were verified, 2024 sample schema/timestamps were verified, and latest REST fallback verified current availability.

## 10. Recommendation

Proceed to a separately approved minimal TIER 1 ingestion task.

Recommended next implementation scope:

1. BTCUSDT and ETHUSDT only.
2. Datasets: `um_klines_1m`, `funding_rate_history`, `premium_index_klines`, `mark_price_klines`, `index_price_klines`.
3. Start with 2024-01-01 to present.
4. Use archive downloads for posted monthly archives and REST fallback for the most recent not-yet-archived period.
5. Produce only raw local data plus manifest, checksums, and gaps report.
6. Do not create H0008 until the ingested data passes gap and point-in-time checks.
