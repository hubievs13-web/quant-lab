---
id: DL0001
slug: derivatives_data_layer_proposal
created: 2026-05-01
status: proposal_only
scope: [BTCUSDT, ETHUSDT]
venue: Binance USD-M Futures
---

# DL0001 - derivatives_data_layer_proposal

## 1. Purpose

V1 relied on QuantConnect-native BTCUSDT and ETHUSDT futures bars. That was enough to test bar-only ideas, but not enough to create genuinely futures-specific edges after H0002, H0005, and H0007 failed. The remaining plausible mechanisms require state variables that describe perpetual positioning or reference-price pressure: funding, predicted funding / premium, open interest, mark price, index price, basis, and signed aggressive flow.

CE0016-CE0020 are the direct evidence. CE0016 needed predicted funding or premium index, CE0017 needed open interest, CE0018 needed mark price, CE0019 needed taker buy/sell flow, and CE0020 showed that ordinary OHLCV/volume alone is too weak and risks becoming disguised short-horizon momentum. Therefore Phase 2 should create a local derivatives data layer before creating H0008. This note is a proposal only. Do not implement ingestion, storage folders, custom QC data, or strategy code without explicit approval.

## 2. Required Data Fields

| Field | Exact meaning | Symbols | Minimum resolution | Required history | Research only or live/paper too |
|---|---|---:|---:|---:|---|
| `perp_ohlcv` | Binance USD-M last-trade futures bars: open, high, low, close, base volume, quote volume, trade count, taker-buy base volume, taker-buy quote volume. | BTCUSDT, ETHUSDT | 1m, resampled to 5m as needed | 2021-01-01 to present preferred; at least 2024-01-01 to present minimum | Research and live/paper |
| `funding_rate_settled` | Real settled funding rate and funding timestamp for the perpetual contract. Positive means longs paid shorts. | BTCUSDT, ETHUSDT | Native funding interval, usually 8h | 2021-01-01 to present preferred; at least 2 years | Research and live/paper if holding near settlement |
| `predicted_funding_rate` | Funding estimate observable before settlement, if captured from exchange mark/premium endpoint; not the final future settled value. | BTCUSDT, ETHUSDT | 1m to 5m snapshots | Needs forward collection unless historical source exists | Research and live/paper |
| `premium_index_klines` | Premium index OHLC for the perp versus reference index, used as a historical proxy for predicted funding pressure. | BTCUSDT, ETHUSDT | 1m or 5m | 2021-01-01 to present preferred | Research and live/paper |
| `open_interest` | Outstanding perpetual position size and notional value at timestamp. | BTCUSDT, ETHUSDT | 5m minimum; 1m if paid vendor supports it | 2021-01-01 to present preferred; public Binance REST is not enough for deep history if limited to latest month | Research and live/paper |
| `mark_price_klines` | OHLC of Binance mark price, not last trade price. Used for liquidation/trigger-price dislocation proxies. | BTCUSDT, ETHUSDT | 1m or 5m | 2021-01-01 to present preferred | Research and live/paper |
| `index_price_klines` | OHLC of Binance index/reference price for BTCUSDT and ETHUSDT pair index. | BTCUSDT, ETHUSDT | 1m or 5m | 2021-01-01 to present preferred | Research and live/paper |
| `basis` | Futures price minus index price and basis rate where exchange provides it. | BTCUSDT, ETHUSDT | 5m minimum | 2021-01-01 to present preferred; public Binance REST may only supply recent windows | Research primarily; live/paper useful |
| `taker_buy_sell_volume` | Buy volume and sell volume from taker-side flow statistics, plus buy/sell ratio. | BTCUSDT, ETHUSDT | 5m minimum | 2021-01-01 to present preferred; public Binance REST may only supply latest 30 days | Research and live/paper |
| `spot_proxy_ohlcv` | Optional BTCUSDT and ETHUSDT spot or index proxy OHLCV to compute independent perp-spot basis if index klines are insufficient. | BTCUSDT, ETHUSDT spot/index proxy | 1m or 5m | Match perp history | Research primarily |

## 3. Data Source Options

### Binance Public REST API

- Availability: Good for klines, funding-rate history, premium index klines, mark price klines, index price klines, current OI, recent OI statistics, recent taker buy/sell volume, and recent basis. Official USD-M endpoints include `/fapi/v1/klines`, `/fapi/v1/fundingRate`, `/fapi/v1/premiumIndexKlines`, `/fapi/v1/markPriceKlines`, `/fapi/v1/indexPriceKlines`, `/futures/data/openInterestHist`, `/futures/data/takerlongshortRatio`, and `/futures/data/basis`.
- Historical coverage: Klines and funding can be paged historically. Binance docs currently state OI statistics, taker buy/sell volume, and basis endpoints return only latest 30 days / 1 month, so they are not enough for multi-year backtests by themselves.
- Free/paid: Free public API.
- Rate limits / operational risk: Public endpoints have request weights and IP limits. Funding shares a 500/5min/IP rate limit with funding info; OI/taker statistics show 1000 requests/5min IP limits in docs. API rules can change.
- Ease of integration: Moderate. Straightforward REST polling, but historical paging, retries, checksum/validation, and timestamp normalization are required.
- QuantConnect backtests: Not directly suitable to call live during backtests. Data should be pre-downloaded and imported as custom data if used inside QC.

### Binance Historical Data Download

- Availability: Official `data.binance.vision` and `binance-public-data` repository provide daily/monthly archives for public market data. Futures klines include taker-buy base/quote volume fields; futures trades and aggTrades are also available.
- Historical coverage: Strong for futures OHLCV/trades/aggTrades. Coverage of funding, OI, premium, mark, index, basis, and taker-statistics must be verified by exact archive path before relying on it. Do not assume unavailable archive types.
- Free/paid: Free public downloads.
- Rate limits / operational risk: Less rate-limit pressure than REST, but archive revisions can occur; checksum validation is required.
- Ease of integration: Best for initial OHLCV bootstrap. Less clear for derivatives state variables beyond klines/trades unless archive paths are confirmed.
- QuantConnect backtests: Yes, after conversion to a compact custom-data CSV/Parquet export and upload/import.

### Paid Data Vendors

- Availability: Vendors such as Coin Metrics and Amberdata advertise historical derivatives data. Coin Metrics documents market open interest with Binance futures coverage, and Amberdata documents Binance futures historical OHLCV and other market-data endpoints. Other vendors may cover funding, OI, basis, liquidations, and order book.
- Historical coverage: Potentially best for deep OI, funding, basis, mark/index, and signed-flow history, but exact Binance USD-M BTCUSDT/ETHUSDT fields must be confirmed before purchase.
- Free/paid: Usually paid for full history; community/free tiers are limited.
- Rate limits / operational risk: Vendor-specific contract, rate limits, schema changes, and redistribution restrictions.
- Ease of integration: Higher data quality and normalized schemas, but account setup and cost add operational burden.
- QuantConnect backtests: Possible only after exporting to custom data. Vendor APIs should not be polled directly inside QC backtests unless the data volume is tiny and terms allow it.

### QuantConnect Custom Data Import

- Availability: QC supports custom data through `PythonData` / `BaseData` with `GetSource` and `Reader`, using chronological CSV or remote files.
- Historical coverage: Whatever we upload or host.
- Free/paid: QC-side storage/hosting constraints depend on the user's plan and chosen hosting path.
- Rate limits / operational risk: Remote custom files add download overhead and hosting reliability risk. Large intraday custom datasets can slow backtests.
- Ease of integration: Moderate for compact 5m features; high complexity for raw 1m multi-file datasets.
- QuantConnect backtests: Yes, this is the main route if strategies must remain in QC.

## 4. Storage Design

This is a proposed layout only. Do not create it until approved.

```text
data/
  raw/
    binance_um/
      klines_1m/
        symbol=BTCUSDT/
        symbol=ETHUSDT/
      funding_rate/
      premium_index_1m/
      mark_price_1m/
      index_price_1m/
      open_interest_5m/
      taker_buy_sell_5m/
      basis_5m/
  processed/
    binance_um/
      features_1m/
      features_5m/
      qc_custom_data/
  manifests/
    source_inventory.csv
    gaps_report.csv
    checksums.csv
```

Recommendation: use Parquet for local research because it preserves types, compresses well, and is efficient for repeated scans. Export CSV only for QC custom data, because CSV is simpler to inspect and aligns with common QC examples. If Parquet dependencies are not approved, use CSV.gz with strict schemas.

Timestamp convention: UTC only. Store `timestamp_open_utc` and `timestamp_close_utc` for bars, and `timestamp_utc` for point-in-time snapshots. All timestamps should be ISO-8601 UTC in exported CSV and integer milliseconds in raw metadata if copied from Binance. No local timezone fields.

Symbol convention: `BTCUSDT` and `ETHUSDT` for Binance USD-M perpetuals. Optional spot proxy must be explicit, for example `BTCUSDT_SPOT_BINANCE` or `BTCUSDT_INDEX_BINANCE`, never overloaded as the perp symbol.

Minimal schemas:

- `perp_ohlcv_1m`: `timestamp_open_utc`, `timestamp_close_utc`, `symbol`, `open`, `high`, `low`, `close`, `volume_base`, `volume_quote`, `trade_count`, `taker_buy_base`, `taker_buy_quote`, `source`, `ingested_at_utc`.
- `funding_rate`: `timestamp_utc`, `symbol`, `funding_rate`, `mark_price_at_funding`, `source`, `ingested_at_utc`.
- `premium_index_1m`: `timestamp_open_utc`, `timestamp_close_utc`, `symbol`, `open`, `high`, `low`, `close`, `source`, `ingested_at_utc`.
- `mark_price_1m`: same bar schema as premium index, with mark-price OHLC.
- `index_price_1m`: same bar schema as premium index, with index-price OHLC.
- `open_interest_5m`: `timestamp_utc`, `symbol`, `open_interest_contracts`, `open_interest_value_usdt`, `source`, `ingested_at_utc`.
- `taker_buy_sell_5m`: `timestamp_utc`, `symbol`, `buy_volume`, `sell_volume`, `buy_sell_ratio`, `source`, `ingested_at_utc`.
- `basis_5m`: `timestamp_utc`, `symbol`, `contract_type`, `futures_price`, `index_price`, `basis`, `basis_rate`, `annualized_basis_rate`, `source`, `ingested_at_utc`.
- `qc_custom_data_5m`: one compact, feature-ready row per symbol per 5m timestamp. Include only fields needed by the selected hypothesis to keep QC backtests light.

## 5. QuantConnect Integration Options

### Option A - Manual CSV Custom Data Upload / Import

Pros:
- Keeps final falsification workflow in QuantConnect.
- Allows derivatives features to be synchronized with QC-native futures bars.
- Best fit once a hypothesis is selected and features are compact.

Cons:
- Requires custom data classes in strategy code later.
- Large 1m files can be slow or fragile in QC.
- Manual hosting/upload path must be maintained.

Leakage risks:
- CSV feature rows must contain only values known at or before `timestamp_utc`.
- Feature generation must not use future bars or final funding values before their timestamp.

Operational complexity: Medium to high.

### Option B - Local Research Only, Later QC Custom Data

Pros:
- Fast iteration on data quality, joins, gap reports, and candidate screening.
- Avoids writing QC strategy code before the data proves useful.
- Allows strict reproducible feature manifests before any hypothesis is promoted.

Cons:
- Local research can diverge from QC fill, fee, and execution assumptions.
- Requires a later porting step and custom-data audit.

Leakage risks:
- Local backtester must enforce signal-on-completed-bar and next-bar execution from the start.
- Feature tables must be point-in-time, not recomputed with future-normalized values.

Operational complexity: Medium. This is the recommended Phase 2 path.

### Option C - Abandon QC For Research Phase, Then Port Final Simple Rules

Pros:
- Maximum flexibility for data joins, Parquet, and vectorized screening.
- Best way to evaluate many derivatives-state mechanisms before spending QC effort.

Cons:
- Higher risk that local results do not survive QC's order/fill model.
- Requires building a local backtest harness, which is outside the current v1 workflow.
- May create process drift unless falsification criteria are mirrored exactly.

Leakage risks:
- Highest risk unless the local engine has explicit timestamp and execution tests.
- Any parameter search must be logged to avoid hidden optimization.

Operational complexity: High.

## 6. Leakage Controls

1. No future funding values. Settled funding at `fundingTime` can only be used for signals whose execution occurs strictly after the funding timestamp and after the data would have been observable.
2. Predicted funding must be captured as a point-in-time snapshot. Do not reconstruct an intraday predicted funding path from the final settled funding rate.
3. Premium, mark, index, OI, basis, and taker-flow fields must be aligned by their own timestamps, not by row index.
4. For any feature row at time `t`, every source value must have source timestamp `<= t`, and strategy execution must be on bar `t+1` or later.
5. No same-bar close-to-close execution. A signal from completed 1m or 5m bar `t` cannot be filled at that same bar close.
6. Multi-symbol features must require BTCUSDT and ETHUSDT timestamps to be explicitly aligned. Missing bars must create no-signal rows, not forward-filled surprises.
7. Resampling from 1m to 5m must close the 5m bar before the signal is eligible. Do not use partial 5m bars.
8. Research splits must be date-pure. OOS data cannot influence thresholds, feature transforms, missing-data decisions, or candidate selection.
9. Every processed dataset must have a gap report and manifest recording source, download time, row count, min/max timestamp, and checksum.

## 7. First Phase 2 Candidate Hypotheses Enabled

These are not H0008. They are future candidates enabled by the proposed data layer.

### Candidate 1 - Premium Compression Repricing

- Mechanism: When premium index is extreme and begins compressing, leveraged crowding may unwind before last-price bars alone show the regime change.
- Required data: premium index klines, perp OHLCV, mark/index price.
- Distinct from H0001-H0007: It uses actual premium pressure, not spot mean reversion, BTC-to-ETH lag, compression breakout, microtrend, wick proxy, Bollinger fade, or settlement clock.
- Why >= 0.10% pre-fee may be plausible: Extreme premium compression can represent direct perp crowding unwind and can plausibly move last price more than a normal 5m candle noise threshold.
- Key falsification risk: Premium may normalize without tradeable last-price movement, or the move may complete before next-bar execution.

### Candidate 2 - OI Absorption Reversal

- Mechanism: Rising OI with poor price progress identifies trapped new leverage; exit pressure from trapped longs/shorts may create reversal.
- Required data: 5m OI snapshots, perp OHLCV, optional taker buy/sell volume.
- Distinct from H0001-H0007: It is not candle reversal or funding timing; it requires confirmed OI expansion and price absorption.
- Why >= 0.10% pre-fee may be plausible: Forced exit of fresh leveraged positions can produce short bursts above the floor, especially on ETHUSDT.
- Key falsification risk: OI expansion may be accumulation before continuation, not trapped flow.

### Candidate 3 - Mark-Last Dislocation Trigger Pressure

- Mechanism: Dislocation between mark price and last trade price can indicate stop/liquidation trigger pressure as mark catches up.
- Required data: mark price klines, perp OHLCV, index price.
- Distinct from H0001-H0007: It uses mark-price mechanics specific to perpetuals, not wick liquidation proxies or scheduled funding unwind.
- Why >= 0.10% pre-fee may be plausible: Trigger-driven flows can be abrupt and larger than ordinary bar-only signals.
- Key falsification risk: Mark-last spread may be too small or update too smoothly to create executable next-bar edge.

### Candidate 4 - Taker Imbalance Aftershock

- Mechanism: Large signed taker imbalance with either price confirmation or price absorption identifies aggressive leveraged flow that can continue or unwind.
- Required data: taker buy volume, taker sell volume, perp OHLCV.
- Distinct from H0001-H0007: It uses signed aggressive futures flow, not generic volume, price momentum, compression, or lead-lag.
- Why >= 0.10% pre-fee may be plausible: Aggressive-flow shocks are closer to the causal order-flow source than OHLCV.
- Key falsification risk: The aftershock may complete inside the signal bar, leaving adverse selection at next-bar execution.

### Candidate 5 - Funding Regime Reversal With Premium Confirmation

- Mechanism: Persistent positive or negative funding plus premium reversal can indicate crowded perp positioning starting to unwind.
- Required data: settled funding history, premium index, perp OHLCV.
- Distinct from H0001-H0007: It uses actual funding and premium state; it is not H0007's bar-only settlement-clock displacement.
- Why >= 0.10% pre-fee may be plausible: Funding crowd unwind can be larger than ordinary price-pattern reversal when premium confirms pressure is changing.
- Key falsification risk: Funding can remain extreme during strong trends, causing repeated contrarian losses.

## 8. Recommendation

Build the Phase 2 data layer proposal into a small approved ingestion project before another hypothesis cycle. Another QC-native researcher cycle is unlikely to produce a valid futures-specific H0008 because OHLCV-only ideas have already failed or become disguised rejected mechanisms. Do not create H0008 until the data access question is resolved.

Recommended sequence:

1. Approve Phase 2 scope for BTCUSDT and ETHUSDT only.
2. Build a minimal data inventory first: confirm exact historical availability for OHLCV, funding, premium, mark, index, OI, taker buy/sell, and basis.
3. If public Binance sources cannot provide at least 12 months of OI/taker/basis history, decide whether to pay a vendor or limit Phase 2 to funding/premium/mark/index hypotheses.
4. Only after a clean point-in-time dataset exists, start a new researcher cycle and create H0008 if a candidate clears data availability, distinct mechanism, and the 0.10% pre-fee edge floor.

## 9. Sources Checked

- Binance USD-M funding rate history: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
- Binance USD-M kline data: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- Binance USD-M premium index klines: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Premium-Index-Kline-Data
- Binance USD-M mark price and mark price klines: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price and https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price-Kline-Candlestick-Data
- Binance USD-M index price klines: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Index-Price-Kline-Candlestick-Data
- Binance USD-M open interest statistics: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics
- Binance USD-M taker buy/sell volume: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Taker-BuySell-Volume
- Binance USD-M basis: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Basis
- Binance public historical data repository: https://github.com/binance/binance-public-data
- QuantConnect custom data documentation: https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/custom-data
- QuantConnect CSV custom data example: https://www.quantconnect.com/docs/v2/writing-algorithms/importing-data/streaming-data/custom-securities/csv-format-example
