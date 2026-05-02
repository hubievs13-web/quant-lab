---
id: DL0003
slug: binance_um_inventory_results
created: 2026-05-01
status: inventory_verification_result
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0003 - binance_um_inventory_results

## 1. Summary

Minimal inventory verification was run for BTCUSDT and ETHUSDT Binance USD-M datasets. The run created only metadata artifacts under `data_inventory/`; it did not download full historical datasets, did not create trading features, did not run a backtest, did not create QuantConnect custom data, and did not create H0008.

The verification environment had intermittent Binance connectivity problems. Several REST requests failed with `_ssl.c:1063: The handshake operation timed out`. Therefore this result is a conservative inventory result: datasets are approved only where both symbol coverage and 12-month feasibility were actually observed in the generated CSV. Expected availability from Binance docs is not treated as approval unless the sample checks verified it.

## 2. Summary Table By Dataset

| Dataset | BTCUSDT result | ETHUSDT result | Final tier classification | 12m free research status | Notes |
|---|---|---|---|---|---|
| `um_klines_1m` | UNKNOWN. 2024 1h sample OK with 60 rows; 2021 archive existence observed; recent REST timed out. | UNKNOWN. REST samples timed out. | UNKNOWN | Not approved yet | Likely available from public archive, but both-symbol verification did not complete. |
| `funding_rate_history` | UNKNOWN. REST samples timed out. | UNKNOWN. 2024 January sample OK with 93 rows; old/recent checks timed out. | UNKNOWN | Not approved yet | Needs rerun or targeted verification because funding is compact and likely feasible, but not verified for both symbols. |
| `premium_index_klines` | UNKNOWN. REST samples timed out; 2021 archive existence observed. | TIER 1. 2021 archive existence and recent timestamp observed, but 2024 REST sample timed out. | UNKNOWN | Not approved yet | One-symbol Tier 1 is not enough for project-level ingestion. |
| `mark_price_klines` | UNKNOWN. REST samples timed out. | UNKNOWN. 2024 1h sample OK and 2021 archive existence observed; recent REST timed out. | UNKNOWN | Not approved yet | Needs both-symbol archive/sample verification. |
| `index_price_klines` | TIER 1. 2024 sample OK; 2021 archive existence observed; recent timestamp observed. | TIER 1. 2024 sample OK; 2021 archive existence observed; recent timestamp observed. | TIER 1 | YES | Approved for later minimal ingestion if Phase 2 ingestion is approved. |
| `open_interest_statistics` | TIER 2. Recent timestamp observed; old/sample checks returned HTTP error. | UNKNOWN. Requests timed out. | TIER 2 / UNKNOWN | NO from Binance REST | Binance docs state latest 1 month only. Requires paid vendor or forward collection for 12-month research. |
| `taker_buy_sell_volume` | UNKNOWN. Requests timed out. | UNKNOWN. HTTP/SSL errors. | UNKNOWN, expected TIER 2 | NO from Binance REST until proven otherwise | Binance docs state latest 30 days only. Requires rerun, paid vendor, or later trade reconstruction plan. |
| `basis` | TIER 2. Recent timestamp observed; old/sample checks failed. | TIER 2. Recent timestamp observed; old/sample checks failed. | TIER 2 | NO from Binance REST | Binance docs state latest 30 days only. Derived basis from perp/index can be considered later, but exchange basis endpoint is not enough. |
| `spot_klines_1m_optional` | UNKNOWN. 2024 sample OK and 2021 archive existence observed; recent REST timed out. | UNKNOWN. REST samples timed out; 2021 archive existence observed. | UNKNOWN | Not approved yet | Optional only; not required if index price is available. |
| `um_agg_trades` | UNKNOWN. Requests timed out. | UNKNOWN. Recent timestamp and 2021 archive existence observed, but 2024 sample timed out. | UNKNOWN | Not approved yet | Availability check only; raw aggTrades are heavy and not approved for ingestion. |

## 3. Final Tier Classification

Approved TIER 1 from this run:

- `index_price_klines` for BTCUSDT and ETHUSDT.

Partial or likely but not approved:

- `um_klines_1m`: BTCUSDT partial success only; ETHUSDT timed out.
- `funding_rate_history`: ETHUSDT 2024 sample success only; BTCUSDT timed out.
- `premium_index_klines`: ETHUSDT classified TIER 1, BTCUSDT unknown.
- `mark_price_klines`: ETHUSDT partial success, BTCUSDT unknown.
- `spot_klines_1m_optional`: partial archive/sample evidence, but optional.

TIER 2 / recent-only or forward-collection class:

- `open_interest_statistics`: at least BTCUSDT showed recent availability; old checks failed and Binance docs state latest 1 month only.
- `basis`: recent timestamps observed for both symbols; old/sample checks failed and Binance docs state latest 30 days only.
- `taker_buy_sell_volume`: expected Tier 2 from docs, but this run did not verify usable samples due request errors.

UNKNOWN:

- Any dataset where both-symbol 12-month availability was not verified because of request failures or missing archive confirmation.

TIER 4:

- Historical liquidation data remains out of scope and unavailable for this project. It was not checked in this run.

## 4. Approved For Later Ingestion

Approved from this run only:

- `index_price_klines`, BTCUSDT and ETHUSDT, 1m.

Not approved yet:

- `um_klines_1m`, `funding_rate_history`, `premium_index_klines`, `mark_price_klines`, `spot_klines_1m_optional`, and `um_agg_trades` need a targeted rerun or archive-only verification because current results are incomplete.

Not approved for 12-month free research from Binance REST:

- `open_interest_statistics`, `basis`, and likely `taker_buy_sell_volume`.

Requires paid vendor or forward collection for 12-month research:

- Historical OI.
- Historical taker buy/sell statistics, unless separately reconstructed from aggTrades/trades after approval.
- Exchange basis endpoint history beyond the latest 30 days.

## 5. Can Free-Only Phase 2 Support Future H0008 Candidates?

Not yet.

Free-only Phase 2 can potentially support future candidates if a targeted rerun verifies both-symbol availability for:

- USD-M perp 1m klines,
- premium index klines,
- mark price klines,
- funding rate history,
- index price klines.

This run verified `index_price_klines` only. Index price alone is not enough for a futures-specific H0008 because it needs to be joined with perp last price, mark price, premium, or funding to define a tradeable pressure mechanism.

OI absorption and taker-flow imbalance candidates are not feasible from free Binance REST for immediate 12-month research based on current docs and this run. They require paid vendor data, forward collection, or a separately approved raw-trade reconstruction path.

## 6. Files Created

- `scripts/verify_binance_um_inventory.py`
- `data_inventory/source_inventory.csv`
- `data_inventory/gaps_report.csv`
- `data_inventory/checksums.csv`
- `obsidian/08_Data_Notes/DL0003_binance_um_inventory_results.md`

No `data/` folder was created. No full market-data archive was downloaded.

## 7. Failed Requests / Errors

Observed request errors in `source_inventory.csv`:

- Multiple REST requests failed with `_ssl.c:1063: The handshake operation timed out`.
- OI old/sample checks returned HTTP errors, consistent with Binance's documented recent-history limitation.
- Some basis checks returned HTTP errors or only recent timestamps, consistent with recent-only endpoint behavior.

The CSV artifacts are the primary record. The note summarizes the result but does not replace the CSV evidence.

## 8. Recommendation

Do not proceed directly to H0008.

Recommended next step: rerun a narrower archive-first verification for likely Tier 1 datasets only:

1. `um_klines_1m`
2. `funding_rate_history`
3. `premium_index_klines`
4. `mark_price_klines`
5. `index_price_klines`

The next run should prefer public archive existence/checksum URLs where possible and use REST only as a fallback, because REST calls were unstable in this environment.

Do not ingest full datasets until both BTCUSDT and ETHUSDT are verified for 2024-01-01 to present. Do not use OI/taker/basis candidates for H0008 unless a paid vendor, forward collection window, or approved trade-reconstruction path is chosen.
