---
id: DL0002
slug: binance_um_data_inventory_plan
created: 2026-05-01
status: inventory_plan_only
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0002 - binance_um_data_inventory_plan

## 1. Objective

Inventory-plan objective: confirm exactly which Binance USD-M datasets are available with enough history for BTCUSDT and ETHUSDT futures research.

Minimum acceptable history: 12 months.

Preferred history: 2021-01-01 to present.

Symbols: BTCUSDT and ETHUSDT only.

This is a plan only. Do not create a `data/` folder, do not download files, do not write ingestion scripts, do not create H0008, do not write strategy code, and do not create QuantConnect custom data yet.

## 2. Dataset Inventory Table

| dataset_id | Field group | Binance endpoint or public archive path to verify | Expected resolution | Expected historical depth | Free or paid | Enough for 12-month research | Enough for QC custom data later | Candidate hypotheses enabled | Blocker notes |
|---|---|---|---|---|---|---|---|---|---|
| `um_klines_1m` | USD-M futures last-trade OHLCV | REST `/fapi/v1/klines`; archive `data/futures/um/monthly/klines/{symbol}/1m/{symbol}-1m-{YYYY}-{MM}.zip` | 1m | Archive likely multi-year; REST pageable | Free | YES if archive has BTCUSDT/ETHUSDT back to target dates | YES after local compression | Baseline for all CE0016-CE0020 descendants | Must validate archive continuity, schema, and checksum. |
| `um_agg_trades` | USD-M futures aggregate trades | REST `/fapi/v1/aggTrades`; archive `data/futures/um/daily/aggTrades/{symbol}/{symbol}-aggTrades-{YYYY}-{MM}-{DD}.zip` and monthly if present | Tick/aggregate trade | Public archive likely multi-year but heavy | Free | UNKNOWN until archive depth and file size are verified | UNKNOWN; probably too heavy raw, useful only for local aggregation | CE0019 if taker-side reconstruction is needed | `isBuyerMaker` allows signed-flow reconstruction, but raw size and timestamp handling are non-trivial. |
| `um_trades` | USD-M futures trades | REST `/fapi/v1/trades`/historical endpoints; archive `data/futures/um/daily/trades/{symbol}/{symbol}-trades-{YYYY}-{MM}-{DD}.zip` and monthly if present | Tick trade | Public archive likely multi-year but heavy | Free | UNKNOWN until archive depth and known corruption/gap risk are verified | NO raw; only compressed features later | CE0019, microstructure diagnostics | Raw trades are operationally heavy; aggTrades may be sufficient. |
| `funding_rate_history` | Settled funding rates | REST `/fapi/v1/fundingRate`; possible archive `data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{YYYY}-{MM}.zip` to verify | Native funding interval, usually 8h | REST appears pageable; archive path must be verified | Free | YES via REST if oldest 2024-01-01 and 2021-01-01 queries return data; UNKNOWN via archive until verified | YES, very compact | CE0016, funding regime reversal with premium confirmation | Settled funding is not predicted funding; cannot use final settlement value before its timestamp. |
| `premium_index_klines` | Premium index OHLC | REST `/fapi/v1/premiumIndexKlines`; archive `data/futures/um/monthly/premiumIndexKlines/{symbol}/1m/{symbol}-1m-{YYYY}-{MM}.zip` | 1m or 5m | Expected multi-year via archive/downloader, must verify exact path | Free | UNKNOWN until 2024 and 2021 archive files or REST oldest paging are verified | YES after compression | CE0016, premium compression repricing, funding+premium | Needed as historical proxy for predicted funding pressure; still not the same as real point-in-time predicted funding snapshots. |
| `mark_price_klines` | Mark price OHLC | REST `/fapi/v1/markPriceKlines`; archive `data/futures/um/monthly/markPriceKlines/{symbol}/1m/{symbol}-1m-{YYYY}-{MM}.zip` | 1m or 5m | Expected multi-year via archive/downloader, must verify exact path | Free | UNKNOWN until archive path/depth verified | YES after compression | CE0018, mark-last dislocation | Critical to avoid replacing mark with last-price OHLC. |
| `index_price_klines` | Index/reference price OHLC | REST `/fapi/v1/indexPriceKlines` with `pair`; archive `data/futures/um/monthly/indexPriceKlines/{symbol}/1m/{symbol}-1m-{YYYY}-{MM}.zip` | 1m or 5m | Expected multi-year via archive/downloader, must verify exact path | Free | UNKNOWN until archive path/depth verified | YES after compression | CE0018, basis/premium models | Endpoint uses `pair`, not necessarily `symbol`; path naming must be verified. |
| `open_interest_statistics` | Historical OI snapshots | REST `/futures/data/openInterestHist` | 5m minimum | Binance docs state latest 1 month only | Free recent; paid needed for full history | NO from Binance REST alone | YES only after paid/vendor or forward-collected history | CE0017 OI absorption reversal | Requires vendor or forward collection for 12-month research. |
| `taker_buy_sell_volume` | Taker buy/sell volume statistics | REST `/futures/data/takerlongshortRatio` | 5m minimum | Binance docs state latest 30 days only | Free recent; paid needed for full history | NO from Binance REST alone | YES only after paid/vendor or forward-collected history | CE0019 taker imbalance aftershock | Alternative: reconstruct from aggTrades/trades, but that is a separate heavy local aggregation task. |
| `basis` | Futures/index basis | REST `/futures/data/basis` with `contractType=PERPETUAL` | 5m minimum | Binance docs state latest 30 days only | Free recent; paid needed for full history | NO from Binance REST alone | YES only after paid/vendor or forward-collected history | Premium/basis dislocation candidates | Can be recomputed from last-price klines and index klines, but exchange basis endpoint history is not enough by itself. |
| `spot_klines_1m_optional` | Optional spot OHLCV proxy | REST `/api/v3/klines`; archive `data/spot/monthly/klines/{symbol}/1m/{symbol}-1m-{YYYY}-{MM}.zip` | 1m | Public archive multi-year expected | Free | YES if archive continuity verified | YES after compression | Basis proxy if index-price data insufficient | Use only as explicit spot proxy; never substitute for index price silently. |

## 3. Verification Commands Plan

Do not execute these yet. They are exact verification methods for the next approved implementation task.

### `um_klines_1m`

- REST template: `https://fapi.binance.com/fapi/v1/klines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500`
- Archive template: `https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- ETH sample query: `https://fapi.binance.com/fapi/v1/klines?symbol=ETHUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- Expected fields: open time, open, high, low, close, volume, close time, quote volume, number of trades, taker-buy base volume, taker-buy quote volume, ignore.
- Oldest timestamp verification: test monthly archive existence for `2021-01`, then binary-search month backward/forward if missing; cross-check REST `startTime=1609459200000`.
- Gap verification: after download, enforce 1m open-time increments; report missing/duplicate bars per symbol-month.
- Schema stability: validate 12 fields and numeric parse for a 2021 file, a 2024 file, and the latest completed month.

### `um_agg_trades`

- REST template: `https://fapi.binance.com/fapi/v1/aggTrades?symbol={SYMBOL}&startTime={START_MS}&endTime={END_MS}&limit=1000`
- Archive template: `https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{YYYY}-{MM}-{DD}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/aggTrades?symbol=BTCUSDT&startTime=1704067200000&endTime=1704067800000&limit=1000`
- ETH sample query: `https://fapi.binance.com/fapi/v1/aggTrades?symbol=ETHUSDT&startTime=1704067200000&endTime=1704067800000&limit=1000`
- Expected fields: aggregate trade id, price, quantity, first trade id, last trade id, timestamp, was buyer maker.
- Oldest timestamp verification: test archive daily/monthly files around `2021-01-01` and `2024-01-01`; document first existing file.
- Gap verification: check timestamp monotonicity, aggregate trade id monotonicity, and no day-level file absence across the selected window.
- Schema stability: parse first, middle, last rows from 2021, 2024, latest file; verify `isBuyerMaker` boolean encoding remains stable.

### `um_trades`

- REST template: `https://fapi.binance.com/fapi/v1/trades?symbol={SYMBOL}&limit=1000` for recent sample; historical verification should prefer archive.
- Archive template: `https://data.binance.vision/data/futures/um/daily/trades/{SYMBOL}/{SYMBOL}-trades-{YYYY}-{MM}-{DD}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/trades?symbol=BTCUSDT&limit=1000`
- ETH sample query: `https://fapi.binance.com/fapi/v1/trades?symbol=ETHUSDT&limit=1000`
- Expected fields: trade id, price, quantity, quote quantity, time, isBuyerMaker.
- Oldest timestamp verification: test archive files for `2021-01-01`, `2024-01-01`, and latest completed day.
- Gap verification: check daily file existence, trade id monotonicity, and timestamp monotonicity; flag known or observed corrupted files.
- Schema stability: compare column counts/types across 2021, 2024, latest files.

### `funding_rate_history`

- REST template: `https://fapi.binance.com/fapi/v1/fundingRate?symbol={SYMBOL}&startTime={START_MS}&endTime={END_MS}&limit=1000`
- Archive template to verify: `https://data.binance.vision/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY}-{MM}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1704067200000&endTime=1706745600000&limit=1000`
- ETH sample query: `https://fapi.binance.com/fapi/v1/fundingRate?symbol=ETHUSDT&startTime=1704067200000&endTime=1706745600000&limit=1000`
- Expected fields: symbol, fundingRate, fundingTime, markPrice.
- Oldest timestamp verification: REST request at `2021-01-01`; if response starts later, record true first funding timestamp. Verify whether public archive path exists.
- Gap verification: funding timestamps should usually step by 8h; flag dynamic interval changes or missing settlements separately.
- Schema stability: validate object keys and numeric parse for 2021, 2024, latest windows.

### `premium_index_klines`

- REST template: `https://fapi.binance.com/fapi/v1/premiumIndexKlines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500`
- Archive template: `https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/premiumIndexKlines?symbol=BTCUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- ETH sample query: `https://fapi.binance.com/fapi/v1/premiumIndexKlines?symbol=ETHUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- Expected fields: open time, open, high, low, close, ignored volume-like fields, close time, ignored fields.
- Oldest timestamp verification: verify archive existence for 2021-01 and 2024-01; fallback to REST paging test.
- Gap verification: enforce 1m open-time increments.
- Schema stability: validate 12-field kline shape and ignored fields across sample years.

### `mark_price_klines`

- REST template: `https://fapi.binance.com/fapi/v1/markPriceKlines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500`
- Archive template: `https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/markPriceKlines?symbol=BTCUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- ETH sample query: `https://fapi.binance.com/fapi/v1/markPriceKlines?symbol=ETHUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- Expected fields: open time, mark open, mark high, mark low, mark close, ignored fields, close time, ignored fields.
- Oldest timestamp verification: verify archive existence for 2021-01 and 2024-01; fallback to REST paging test.
- Gap verification: enforce 1m open-time increments; compare first/last timestamps against perp klines.
- Schema stability: validate 12-field kline shape and numeric OHLC parse.

### `index_price_klines`

- REST template: `https://fapi.binance.com/fapi/v1/indexPriceKlines?pair={PAIR}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500`
- Archive template: `https://data.binance.vision/data/futures/um/monthly/indexPriceKlines/{PAIR}/1m/{PAIR}-1m-{YYYY}-{MM}.zip`
- BTC sample query: `https://fapi.binance.com/fapi/v1/indexPriceKlines?pair=BTCUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- ETH sample query: `https://fapi.binance.com/fapi/v1/indexPriceKlines?pair=ETHUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1500`
- Expected fields: open time, index open, index high, index low, index close/latest, ignored fields, close time, ignored fields.
- Oldest timestamp verification: verify archive existence for 2021-01 and 2024-01; fallback to REST paging test.
- Gap verification: enforce 1m open-time increments; compare with mark and premium series.
- Schema stability: validate `pair` naming and 12-field kline shape across years.

### `open_interest_statistics`

- REST template: `https://fapi.binance.com/futures/data/openInterestHist?symbol={SYMBOL}&period=5m&startTime={START_MS}&endTime={END_MS}&limit=500`
- Archive template: none confirmed from official Binance public archive in DL0001; verify manually only if an official path is found.
- BTC sample query: `https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&startTime=1704067200000&endTime=1704153600000&limit=500`
- ETH sample query: `https://fapi.binance.com/futures/data/openInterestHist?symbol=ETHUSDT&period=5m&startTime=1704067200000&endTime=1704153600000&limit=500`
- Expected fields: symbol, sumOpenInterest, sumOpenInterestValue, timestamp, optional CMCCirculatingSupply.
- Oldest timestamp verification: intentionally query more than 1 month back and record whether Binance returns empty/error/recent-only data.
- Gap verification: for recent month, enforce 5m timestamp increments; for historical, mark NO if unavailable.
- Schema stability: compare recent samples across both symbols; if paid vendor is used later, separately validate vendor schema.

### `taker_buy_sell_volume`

- REST template: `https://fapi.binance.com/futures/data/takerlongshortRatio?symbol={SYMBOL}&period=5m&startTime={START_MS}&endTime={END_MS}&limit=500`
- Archive template: none confirmed from official Binance public archive.
- BTC sample query: `https://fapi.binance.com/futures/data/takerlongshortRatio?symbol=BTCUSDT&period=5m&startTime=1704067200000&endTime=1704153600000&limit=500`
- ETH sample query: `https://fapi.binance.com/futures/data/takerlongshortRatio?symbol=ETHUSDT&period=5m&startTime=1704067200000&endTime=1704153600000&limit=500`
- Expected fields: buySellRatio, buyVol, sellVol, timestamp.
- Oldest timestamp verification: intentionally query more than 30 days back and record true behavior.
- Gap verification: for recent data, enforce 5m timestamps.
- Schema stability: compare BTCUSDT and ETHUSDT recent samples; if reconstructing from aggTrades, define a separate derived schema.

### `basis`

- REST template: `https://fapi.binance.com/futures/data/basis?pair={PAIR}&contractType=PERPETUAL&period=5m&startTime={START_MS}&endTime={END_MS}&limit=500`
- Archive template: none confirmed from official Binance public archive.
- BTC sample query: `https://fapi.binance.com/futures/data/basis?pair=BTCUSDT&contractType=PERPETUAL&period=5m&startTime=1704067200000&endTime=1704153600000&limit=500`
- ETH sample query: `https://fapi.binance.com/futures/data/basis?pair=ETHUSDT&contractType=PERPETUAL&period=5m&startTime=1704067200000&endTime=1704153600000&limit=500`
- Expected fields: indexPrice, contractType, basisRate, futuresPrice, annualizedBasisRate, basis, pair, timestamp.
- Oldest timestamp verification: intentionally query more than 30 days back and record true behavior.
- Gap verification: for recent data, enforce 5m timestamps.
- Schema stability: compare against derived basis from perp close and index close for overlapping recent windows.

### `spot_klines_1m_optional`

- REST template: `https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1000`
- Archive template: `https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip`
- BTC sample query: `https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1000`
- ETH sample query: `https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1m&startTime=1704067200000&endTime=1704153600000&limit=1000`
- Expected fields: open time, open, high, low, close, volume, close time, quote asset volume, number of trades, taker-buy base volume, taker-buy quote volume, ignore.
- Oldest timestamp verification: verify archive existence for 2021-01 and 2024-01.
- Gap verification: enforce 1m open-time increments.
- Schema stability: note Binance public-data README says spot timestamps from 2025-01-01 onward are microseconds; normalize explicitly if used.

## 4. Decision Matrix

TIER 1 - usable now for 12+ month research from free sources:

- `um_klines_1m`: expected Tier 1 after archive verification.
- `funding_rate_history`: expected Tier 1 via REST paging if old timestamps return data.
- `premium_index_klines`: expected Tier 1 if official archive path verifies for 2024 and 2021.
- `mark_price_klines`: expected Tier 1 if official archive path verifies for 2024 and 2021.
- `index_price_klines`: expected Tier 1 if official archive path verifies for 2024 and 2021.
- `spot_klines_1m_optional`: expected Tier 1 after archive verification.

TIER 2 - usable only for recent data / forward collection:

- `open_interest_statistics`: Binance docs state latest 1 month only.
- `taker_buy_sell_volume`: Binance docs state latest 30 days only.
- `basis`: Binance docs state latest 30 days only.

TIER 3 - requires paid vendor for 12+ month research:

- Historical OI at 5m or better if not available in an official public archive.
- Historical taker buy/sell statistics if not reconstructed from aggTrades/trades.
- Historical basis if exchange endpoint's 30-day limit is insufficient and derived basis is not accepted.
- Any normalized cross-source derivatives dataset with SLA, if public archives prove incomplete.

TIER 4 - unavailable / reject:

- Historical liquidation data for this project remains rejected unless a reliable approved vendor is chosen later.
- Reconstructed predicted funding from future settled funding is rejected as leakage.
- Any dataset that cannot produce source timestamps, schema, and a gap report is rejected for hypothesis research.

## 5. Research Implications

Free-only data:

- Feasible if Tier 1 verifies: premium compression repricing, mark-last dislocation, funding regime plus premium confirmation, and derived basis using perp/index prices.
- Not feasible from Binance REST alone: OI absorption reversal and taker-statistics hypotheses requiring 12 months of OI/taker-statistics.
- Possible but heavy: reconstruct signed taker pressure from aggTrades/trades if archives are complete and local aggregation is later approved.

Free + forward collection:

- Feasible after waiting: OI/taker/basis forward datasets can accumulate from today onward, but cannot support immediate 12-month historical falsification.
- Useful for paper/live diagnostics later, not enough for current H0008 research unless the project accepts delayed validation.

Paid vendor:

- Feasible: OI absorption reversal, taker imbalance aftershock, normalized basis/premium/OI models, and more robust derivatives-state hypotheses.
- Required if public Binance archives do not cover 12+ months of OI/taker/basis and if those candidates remain priority.

QC custom data only after local feature compression:

- Raw 1m or tick data should not be pushed into QC first.
- Local inventory and feature compression should produce compact 5m point-in-time rows only after a candidate is selected.
- QC custom data should be a final validation path, not the first place to discover data quality problems.

## 6. Minimal Next Implementation Scope

If approved later, the smallest possible ingestion task is:

1. Scope only BTCUSDT and ETHUSDT.
2. Use only TIER 1 datasets after verification: `um_klines_1m`, `funding_rate_history`, `premium_index_klines`, `mark_price_klines`, `index_price_klines`, and optional `spot_klines_1m_optional`.
3. Initial date range: 2024-01-01 to present.
4. Produce only inventory artifacts: `manifest`, `checksums`, and `gaps_report`.
5. Do not backtest.
6. Do not create H0008.
7. Do not build QC custom data.
8. Do not ingest TIER 2/TIER 3 datasets until their history decision is resolved.

The implementation must be separately approved. This note does not authorize writing scripts or downloading data.

## 7. Leakage Controls

1. No final funding before timestamp. A settled funding value may be used only after its `fundingTime` and only for execution on a later bar.
2. No reconstructed predicted funding from future settled funding. Historical predicted funding must come from point-in-time premium/funding snapshots, not hindsight settlement values.
3. Timestamp alignment must use source timestamps, not row index.
4. Strategy execution model remains signal on completed bar `t`, execution on bar `t+1` or later.
5. No same-bar close-to-close execution.
6. No OOS influence in feature selection, threshold selection, missing-data policy, or schema decisions.
7. Gaps must create missing/no-signal states unless a hypothesis explicitly defines a non-leaky fill rule before testing.
8. Multi-symbol joins must require explicit BTCUSDT and ETHUSDT timestamp alignment.

## 8. Sources To Use During Verification

- Binance USD-M kline REST docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- Binance USD-M funding REST docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
- Binance USD-M premium index kline docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Premium-Index-Kline-Data
- Binance USD-M mark price kline docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price-Kline-Candlestick-Data
- Binance USD-M index price kline docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Index-Price-Kline-Candlestick-Data
- Binance USD-M OI statistics docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics
- Binance USD-M taker buy/sell volume docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Taker-BuySell-Volume
- Binance USD-M basis docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Basis
- Binance public data README: https://github.com/binance/binance-public-data
- Binance public archive browser: https://data.binance.vision/
