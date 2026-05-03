# Data Layer Implementation Plan

Plan-only document. No code, no data download. Each implementation
phase is a separate, gated PR (see Section 14).

## 0. Purpose and constraints

A file-based Market Research Data Layer for crypto futures research
that lets Codex / Devin propose hypotheses from compact, evidence-
backed summaries instead of intuition. The Data Layer never sets
verdicts, never edits strategy code, and never edits
`experiments_log.md`, `results/experiments.csv`, or any protected
file under `.codex/`, `MASTER_CONTEXT.md`, `PROJECT_INSTRUCTIONS.md`,
`README.md`, or `obsidian/01_Rules/` through
`obsidian/10_Codex_Instructions/`.

Hard constraints (carried forward from the user spec):

- Plain Python + local Parquet / CSV + Markdown only.
- No RAG, vector DB, MCP, web app, Docker, DB server, or any new
  heavy infra.
- Public exchange endpoints only; no private API key in v1.
- All raw / processed bulk files are gitignored and
  do-not-read-by-default.
- Codex reads only summaries and reports under
  `data_layer/reports/`, never raw Parquet.
- v1 runs locally on the user's machine; no cloud component.

## 1. Final folder structure

```
data_layer/
  DATA_LAYER_IMPLEMENTATION_PLAN.md       # this file
  README.md                               # added in Phase 1

  config/
    universe.yaml                         # symbols, timeframes, history windows
    sources.yaml                          # endpoint, ratelimit, retry per exchange
    features.yaml                         # feature definitions
    regimes.yaml                          # regime threshold parameters
    events.yaml                           # event detection parameters

  ingest/
    __init__.py
    common.py                             # rate-limit + retry + checksum helpers
    binance/
      ohlcv.py
      funding.py
      open_interest.py
      mark_index.py
      taker_volume.py
      long_short_ratio.py
      liquidations.py                     # WS-only in v1, see Section 3
    bybit/...                             # deferred / out of scope
    okx/...                               # deferred / out of scope

  process/
    align.py                              # bar resampling and timestamp alignment
    join.py                               # left-join derivatives onto OHLCV bar grid
    features.py                           # feature engineering (no lookahead)
    regimes.py                            # regime label engine
    events.py                             # event detection engine
    outcomes.py                           # forward returns + MFE/MAE
    quality.py                            # data quality checks
    leaderboard.py                        # event leaderboard

  store/                                  # GITIGNORED, do-not-read-by-default
    raw/
      binance/{ohlcv,funding,oi,mark,index,premium,taker,lsr,liquidations}/
        BTCUSDT/{5m,1h}/YYYY/MM/*.parquet
        ETHUSDT/{5m,1h}/YYYY/MM/*.parquet
    processed/
      bars/{exchange}/{symbol}/{timeframe}.parquet
      features/{exchange}/{symbol}/{timeframe}.parquet
      regimes/{exchange}/{symbol}/{timeframe}.parquet
      events/{exchange}/{symbol}/{timeframe}.parquet
      outcomes/{exchange}/{symbol}/{timeframe}.parquet
      leaderboard/{exchange}/{symbol}/{timeframe}.parquet
    quality/
      {exchange}/{symbol}/{timeframe}/YYYY-MM-DD.json

  reports/                                # COMMITTED, small markdown only
    quality/
      latest_summary.md
      <YYYY-MM-DD>_<exchange>_<symbol>_<tf>.md
    leaderboards/
      latest_event_leaderboard.md
      <YYYY-MM-DD>_event_leaderboard.md
    summaries/                            # the Codex-readable layer
      universe_status.md
      regime_summary.md
      event_catalog.md
      feature_catalog.md
      outcome_summary.md
      hypothesis_seed_briefs/
        seed_<topic>.md
    INGEST_LOG.md                         # append-only fetch log

  scripts/
    cli.py                                # `python -m data_layer.cli <cmd>`
    fetch.py                              # one-shot fetcher per source
    rebuild.py                            # rebuild processed/* from raw/*
    refresh_summaries.py                  # regenerate reports/summaries/*
```

Notes:

- `data_layer/store/` is gitignored. Everything under it is bulk data.
- `data_layer/reports/` is committed but capped: each markdown < 5 KB,
  each report folder < ~1 MB total. Markdown is the only thing
  Codex reads.
- All ingest / process modules write Parquet using a fixed schema
  (see Section 2).

## 2. Table schemas

All times are UTC, integer ms epoch in `ts_open_ms` and
`ts_close_ms`. Bar-row convention: each row covers
`[ts_open_ms, ts_close_ms)` (close exclusive). All numeric fields
are `float64` unless noted.

### 2.1 raw/ohlcv

| col | type | notes |
|---|---|---|
| ts_open_ms | int64 | bar open epoch ms |
| ts_close_ms | int64 | bar close epoch ms |
| open, high, low, close | f64 | quote currency |
| volume_base | f64 | base asset traded |
| volume_quote | f64 | quote asset traded |
| trades | int64 | nullable |
| exchange | str | enum {binance} |
| symbol | str | e.g. BTCUSDT |
| timeframe | str | enum {5m, 1h} |

### 2.2 raw/funding

| col | type | notes |
|---|---|---|
| ts_settle_ms | int64 | actual settlement time |
| funding_rate | f64 | per period (e.g. 8h) |
| funding_interval_ms | int64 | exchange-declared, default 8h |
| predicted_funding_rate | f64 | nullable; from predicted endpoint if available |
| exchange, symbol | str | as above |

### 2.3 raw/open_interest

| col | type | notes |
|---|---|---|
| ts_ms | int64 | sample time |
| oi_base | f64 | open interest in base asset |
| oi_value_quote | f64 | open interest in quote (if reported) |
| exchange, symbol | str | |

### 2.4 raw/mark_index

| col | type | notes |
|---|---|---|
| ts_ms | int64 | |
| mark_price | f64 | |
| index_price | f64 | |
| exchange, symbol | str | |

### 2.5 raw/taker_volume

| col | type | notes |
|---|---|---|
| ts_open_ms, ts_close_ms | int64 | window |
| taker_buy_base, taker_sell_base | f64 | |
| taker_buy_quote, taker_sell_quote | f64 | |
| exchange, symbol, timeframe | str | |

### 2.6 raw/long_short_ratio

| col | type | notes |
|---|---|---|
| ts_ms | int64 | |
| long_short_account_ratio | f64 | nullable |
| long_short_position_ratio | f64 | nullable |
| top_trader_ratio | f64 | nullable; where exchange splits it |
| exchange, symbol | str | |

### 2.7 raw/liquidations

| col | type | notes |
|---|---|---|
| ts_ms | int64 | event timestamp |
| side | str | 'long' or 'short' |
| price | f64 | |
| qty_base | f64 | |
| qty_quote | f64 | nullable |
| exchange, symbol | str | |

### 2.8 processed/bars (canonical aligned grid)

OHLCV joined with derivatives onto the bar grid. Left-join semantics.
Funding is forward-filled within funding interval; OI / mark / index
/ LSR are forward-filled with TTL = 60 minutes; taker volume is
per-bar (not ffilled); liquidations are aggregated per bar.

Columns: all `raw/ohlcv` columns, plus:

| col | type | notes |
|---|---|---|
| funding_rate_ffill | f64 | last known funding rate |
| funding_minutes_to_next | f64 | minutes until next settle |
| premium | f64 | mark - index |
| basis_bp | f64 | (mark - index) / index * 1e4 |
| oi_base, oi_value_quote | f64 | ffilled |
| oi_change_pct_1h | f64 | derived feature, see Section 4 |
| taker_buy_base, taker_sell_base | f64 | per bar |
| taker_imbalance | f64 | (buy - sell) / (buy + sell) |
| lsr_account, lsr_position | f64 | ffilled |
| liq_long_qty_base, liq_short_qty_base | f64 | per bar |
| has_funding_settle | int8 | 1 if a funding settle falls in this bar |

### 2.9 processed/features

All Section 4 features keyed by
`(exchange, symbol, timeframe, ts_open_ms)`.

### 2.10 processed/regimes

| col | type |
|---|---|
| ts_open_ms | int64 |
| trend_regime | str enum |
| vol_regime | str enum |
| funding_regime | str enum |
| basis_regime | str enum |
| crowding_regime | str enum |
| liquidity_regime | str enum |
| composite_label | str |
| confidence | f64 in [0,1] |

### 2.11 processed/events

| col | type |
|---|---|
| event_id | str (uuid) |
| ts_open_ms | int64 |
| event_type | str enum (Section 6) |
| event_strength | f64 (z-score units) |
| context_regime | str |
| symbol, exchange, timeframe | str |

### 2.12 processed/outcomes

| col | type |
|---|---|
| event_id | str |
| horizon | str enum {h+1, h+3, h+12, h+24, h+72} |
| forward_return_pct | f64 |
| mfe_pct | f64 |
| mae_pct | f64 |
| time_to_mfe_bars | int32 |
| time_to_mae_bars | int32 |
| max_holding_bars_used | int32 |

### 2.13 processed/leaderboard

Aggregations over events: per `event_type`, per `regime`, per
horizon: `count`, `mean_forward_return`, `hit_rate_at_zero`,
`median_mfe`, `median_mae`, `mfe_mae_ratio`, `sharpe_like`. Source
for `reports/leaderboards/*.md`.

### 2.14 quality/<...>.json

| field | type |
|---|---|
| date_utc | str |
| exchange, symbol, timeframe | str |
| expected_bars | int |
| received_bars | int |
| missing_bars | int |
| duplicate_bars | int |
| out_of_order_rows | int |
| zero_volume_bars | int |
| funding_rows_received | int |
| funding_rows_expected | int |
| oi_gap_max_minutes | f64 |
| premium_outliers_count | int |
| ts_drift_max_ms | int |

## 3. Data sources by exchange

All public, documented endpoints. No API key for v1. Documentation
URLs are pinned in `data_layer/config/sources.yaml`.

### 3.1 Binance USD-M futures (primary)

- OHLCV: `GET /fapi/v1/klines`
- Funding rate history: `GET /fapi/v1/fundingRate`
- Predicted funding: `GET /fapi/v1/premiumIndex` (premium component)
  + `GET /fapi/v1/fundingInfo` for the next interval
- Mark + index price: `GET /fapi/v1/premiumIndex`
- Open interest history: `GET /futures/data/openInterestHist`
  (5m / 15m / 30m / 1h / 2h / 4h / 6h / 12h / 1d)
- Long/short ratio: `GET /futures/data/globalLongShortAccountRatio`,
  `topLongShortAccountRatio`, `topLongShortPositionRatio`
- Taker buy/sell volume: `GET /futures/data/takerlongshortRatio`
- Liquidations: not in public REST for arbitrary history; in v1 we
  capture WS `<sym>@forceOrder` snapshots only when the user runs
  the streamer. Historical backfill deferred to v2.

### 3.2 Bybit (deferred / out of scope)

Bybit is not part of the active project scope. Do not implement or
ingest Bybit unless the user explicitly re-approves it later.

### 3.3 OKX (deferred / out of scope)

OKX is not part of the active project scope. Do not implement or
ingest OKX unless the user explicitly re-approves it later.

Binance ingest modules normalize to the schemas in Section 2. Any
field not natively returned is null and surfaced in the quality report
(Section 8).

## 4. Exact feature list

All features evaluated at `ts_close_ms`. No future bar referenced.
Lookback windows are in bars at the row's own timeframe.

A. Price / return

- `ret_1`, `ret_3`, `ret_12`, `ret_72`: log returns over N bars.
- `vol_close_to_close_24`: rolling stdev of `ret_1` over 24 bars.
- `parkinson_vol_24`: Parkinson estimator over 24 bars.
- `atr_14`: ATR over 14 bars.
- `range_pct`: `(high - low) / open`.

B. Trend

- `ema_fast_minus_slow_pct = (EMA12 - EMA48) / close`.
- `slope_ret_24`: linreg slope of `close` over 24 bars in pct/bar.
- `adx_14`: ADX over 14 bars.

C. Volume / flow

- `vol_zscore_24`: z-score of `volume_quote` over 24 bars.
- `taker_imbalance` (already in processed/bars).
- `taker_imbalance_ema_12`.
- `taker_quote_zscore_24`: z-score of
  `taker_buy_quote + taker_sell_quote`.

D. Funding / basis

- `funding_rate_ffill`, `funding_rate_zscore_30d`.
- `predicted_funding_minus_realized` (when predicted is available).
- `funding_minutes_to_next`.
- `basis_bp`, `basis_bp_zscore_24`, `basis_bp_zscore_30d`.
- `funding_basis_alignment = sign(funding_rate) * sign(basis_bp)`
  in {-1, 0, 1}.

E. Open interest

- `oi_pct_change_1h`, `oi_pct_change_24h`.
- `oi_zscore_30d`.
- `oi_vs_price_divergence_24`: sign of correlation of `oi` vs
  `close` over 24 bars in {-1, 0, 1}.

F. Crowding (long/short ratio)

- `lsr_account_z_30d`, `lsr_position_z_30d`.
- `lsr_account_extreme = abs(z) > 2`.

G. Liquidations

- `liq_long_qty_base_zscore_24`, `liq_short_qty_base_zscore_24`.
- `liq_long_minus_short_imbalance_24h`.

H. Microstructure / session

- `is_funding_window_pre_30m` flag.
- `is_funding_window_post_30m` flag.
- `time_of_day_bucket` enum {asia, london, ny, off}.
- `weekday` 0..6.

The full machine-readable list is regenerated into
`data_layer/reports/summaries/feature_catalog.md` so Codex never
scans code to enumerate features.

## 5. Market regime definitions

Categorical labels per bar. Each axis is independent. Composite
label is the tuple. Thresholds live in
`data_layer/config/regimes.yaml`.

- `trend_regime`:
  - `up_trend` if `ema_fast_minus_slow_pct > 0`,
    `slope_ret_24 > 0`, and `adx_14 >= 20`.
  - `down_trend` mirror.
  - else `chop`.
- `vol_regime`: bucket `vol_close_to_close_24` over 30d rolling
  window into `low` (<= 33rd pct), `mid`, `high` (> 66th pct).
- `funding_regime`:
  - `pos_extreme` if `funding_rate_zscore_30d > 2`.
  - `neg_extreme` if `< -2`.
  - `pos_normal` / `neg_normal` by sign.
  - `flat` if `abs(rate) <= 1 bp`.
- `basis_regime`:
  - `premium_rich` if `basis_bp_zscore_30d > 2`.
  - `discount_rich` if `< -2`.
  - else `neutral`.
- `crowding_regime`:
  - `long_crowded` if `lsr_account_z_30d > 2`.
  - `short_crowded` if `< -2`.
  - else `balanced`.
- `liquidity_regime`: from `taker_quote_zscore_24` and
  `oi_zscore_30d` jointly: `thin`, `normal`, `thick`.

All thresholds are timestamped in the regime parquet so historical
labels are reproducible after any threshold change.

## 6. Market event definitions

Events are discrete points in time with `event_type` and
`event_strength`. One row per event in `processed/events`. Detected
from the aligned bar grid only (no future bar references).
Parameters live in `data_layer/config/events.yaml`.

- `EV_FUND_FLIP`: `sign(funding_rate)` flips between two
  consecutive funding intervals.
- `EV_FUND_EXTREME`: `funding_rate_zscore_30d` first crosses
  `> +2` or `< -2`.
- `EV_PREMIUM_SPIKE`: `basis_bp_zscore_24` first crosses `> +3`.
- `EV_PREMIUM_COMPRESSION`: `basis_bp_zscore_24` first crosses
  `< -3` from positive premium territory.
- `EV_OI_SPIKE_UP`: `oi_pct_change_1h > +3%` AND
  `oi_zscore_30d > 1`.
- `EV_OI_FLUSH`: `oi_pct_change_1h < -3%`.
- `EV_LIQ_LONG_CASCADE`: `liq_long_qty_base_zscore_24 > 3`.
- `EV_LIQ_SHORT_CASCADE`: `liq_short_qty_base_zscore_24 > 3`.
- `EV_VOL_BREAKOUT`: `range_pct` > 99th pct over 30d AND
  `taker_quote_zscore_24 > 2`.
- `EV_CROWD_FLIP`: `lsr_account_z_30d` flips from `> +1.5` to
  `< -1.5` (or mirror) within 24 bars.
- `EV_FUNDING_WINDOW_PRE`: 30 minutes before a funding settle
  (informational, not a signal alone).

`event_strength` is in absolute z-score units so events of the
same type are comparable across regimes.

## 7. Forward outcome definitions

For each event, compute fixed-horizon outcomes anchored on the bar
that closes strictly **after** the event bar (no same-bar
contamination, see Section 13). No partial bars.

Horizons:

- 5m grid: `h+1` (5m), `h+3` (15m), `h+12` (1h), `h+72` (6h).
- 1h grid: `h+1` (1h), `h+3` (3h), `h+12` (12h), `h+24` (1d),
  `h+72` (3d).

Per (event, horizon):

- `forward_return_pct = (close[t+h] - close[t]) / close[t] * 100`.
- `mfe_pct` = max over `(t, t+h]` of `(high - close_t) / close_t`.
- `mae_pct` = min over `(t, t+h]` of `(low - close_t) / close_t`.
- `time_to_mfe_bars`, `time_to_mae_bars`: bar offsets from `t`.
- Direction-adjusted views are out of scope for weak WATCHLIST-only
  `EV_VOL_BREAKOUT` signals unless explicitly re-approved later.

## 8. Data quality checks

Run by `process/quality.py` after each ingest. Output: one JSON per
(date, exchange, symbol, tf) under `store/quality/` plus a markdown
roll-up at `reports/quality/latest_summary.md`.

- Bar count matches `expected_bars = day_seconds / tf_seconds`.
- No duplicate `ts_open_ms` per (exchange, symbol, tf).
- Timestamps strictly monotonic per series.
- Funding row count matches expected per `funding_interval_ms`.
- OI sample gap < 60 minutes for 5m grid; < 4h for 1h grid.
- Premium / basis outliers: `basis_bp_zscore_24 > 6` flagged.
- `volume == 0` for > 5 consecutive bars flagged.
- Mark vs index drift sanity: `abs(mark/index - 1) > 5%` flagged.
- Funding rate sanity: `abs(funding_rate) > 0.5%` flagged.
- Server / local clock drift at fetch time within 5 s; otherwise
  flagged.
- Schema check: each parquet has the expected columns and dtypes;
  failures mark the run `failed_schema` and block promotion to
  `processed/`.

The markdown roll-up is the only thing Codex reads. It is short:
green / yellow / red counts per series plus the top three issues.

## 9. Storage format policy

- Parquet (snappy compression). ZStandard allowed if already
  installed by the user.
- Raw OHLCV: one Parquet per (exchange, symbol, timeframe, year,
  month).
- Raw derivatives: one Parquet per (exchange, symbol, year-month).
- Processed tables: one Parquet per (exchange, symbol, timeframe),
  rewritten incrementally.
- Every Parquet has a sibling `.checksum` file with sha256.
- Markdown reports: UTF-8, no HTML, < 5 KB each.
- No SQLite, no DuckDB file, no LMDB. v1 stays Parquet-only to
  avoid hidden lock files and DB drivers.
- File naming is lower-snake-case, except symbols which retain
  exchange casing (`BTCUSDT`, not `btcusdt`).

## 10. Gitignore policy for large data

Add to `.gitignore`:

```
# Market Research Data Layer
data_layer/store/
*.parquet
*.parquet.checksum
data_layer/.cache/
```

`*.feather`, `*.h5`, `*.hdf5`, `*.csv` are already gitignored
repo-wide (with `results/experiments.csv` whitelisted). The
existing repo-wide `*.csv` ignore is sufficient for any CSV byproduct
of the Data Layer.

Whitelisting (explicitly tracked):

- `data_layer/reports/**` (small markdown reports).
- `data_layer/config/**`.
- All `data_layer/**/*.md`, `data_layer/**/*.py`,
  `data_layer/**/*.yaml`.

LFS is not used in v1.

## 11. How Codex should use the Data Layer without wasting tokens

Default read order for any data-layer-related question:

1. `data_layer/reports/summaries/universe_status.md` — what is
   loaded, freshness, any red quality flags.
2. `data_layer/reports/summaries/regime_summary.md` — current
   regime per (exchange, symbol, tf).
3. `data_layer/reports/summaries/event_catalog.md` — event
   definitions + counts.
4. `data_layer/reports/summaries/feature_catalog.md` — feature
   definitions + ranges.
5. `data_layer/reports/leaderboards/latest_event_leaderboard.md`
   — top events ranked by forward edge.
6. `data_layer/reports/quality/latest_summary.md` — flagged days
   only.
7. `data_layer/reports/summaries/hypothesis_seed_briefs/<topic>.md`
   — short briefs Codex consumes when proposing a new hypothesis.

Forbidden by default (need explicit user approval to read):

- `data_layer/store/**`, including all raw and processed Parquet.
- Any file > 5 MB.
- The full feature parquet (use `feature_catalog.md` instead).

The seven summaries above are append-only and capped (each
< 5 KB), regenerated by `scripts/refresh_summaries.py`. Codex
never reads Parquet directly; if a Parquet read is the only way to
answer, Codex must ask the user to run
`python -m data_layer.cli query <name> --json` and then read the
produced markdown answer.

The Data Layer adds one append-only line to
`obsidian/00_INGEST_LOG.md` per refresh (Phase 6 only) so the wiki
stays aligned. It does not modify any other wiki file.

## 12. Phased implementation steps

Each phase = one PR, gated by user approval (Section 14).

### Phase 1: scaffold (NO data download)

- Create `data_layer/` skeleton: `config/`, `ingest/`, `process/`,
  `scripts/`, `reports/summaries/`, `reports/quality/`,
  `reports/leaderboards/`, plus `data_layer/README.md`.
- Add `data_layer/config/{universe,sources,features,regimes,events}.yaml`
  with the values in Sections 1, 4, 5, 6.
- Add the `.gitignore` block (Section 10) and verify nothing under
  `store/` would be committed.
- Add `data_layer/scripts/cli.py` with subcommand stubs that print
  "not implemented".
- Pure file scaffolding. No network call. No new Python dependency.

### Phase 2: Binance OHLCV + funding + OI (smoke)

- Implement `ingest/binance/{ohlcv,funding,open_interest}.py`
  against documented public endpoints.
- Smoke-fetch BTCUSDT 5m for 7 days, 1h for 30 days, into
  `store/raw/`.
- Implement `process/{align,join,quality}.py` minimal path:
  produce `store/processed/bars/binance/BTCUSDT/5m.parquet` and a
  quality JSON + the markdown roll-up.
- Update `reports/summaries/universe_status.md`.
- New deps as needed (likely just `requests`, `pandas`, `pyarrow`).

### Phase 3: full Binance derivatives + features + regimes

- Add `mark_index`, `taker_volume`, `long_short_ratio` ingestors.
- Implement `process/features.py` and `process/regimes.py`.
- Generate `feature_catalog.md`, `regime_summary.md`.

### Phase 4: events + outcomes + leaderboard

- Implement `process/{events,outcomes,leaderboard}.py`.
- Generate `event_catalog.md`,
  `latest_event_leaderboard.md`, `outcome_summary.md`.

### Phase 5: deferred cross-exchange mirrors

- Bybit and OKX are deferred and out of scope unless the user
  explicitly re-approves them later.
- Next active Data Layer validation target is Binance ETHUSDT using
  the existing Binance path. Do not ingest or create data without
  approval for that run.

### Phase 6: hypothesis seed briefs

- `scripts/refresh_summaries.py` writes
  `reports/summaries/hypothesis_seed_briefs/seed_<topic>.md` for
  the top-N events from the leaderboard. Each brief: ~150 lines,
  includes regime context, forward-return distribution, MFE / MAE
  percentiles, and a distinctness check vs rejected H0001..H0007
  per `.codex/AGENTS.md` Section 10.
- Append a single line to `obsidian/00_INGEST_LOG.md` per refresh.

### Phase 7 (optional, deferred): liquidations + order book

- WS streamer for Binance forceOrder only. Bybit and OKX liquidation
  streams are deferred out of scope unless explicitly re-approved.
- Order book snapshots only after explicit user approval; large
  data, gitignored, opt-in.

## 13. Risks and anti-lookahead rules

- Closed-bar values only. Bar at `ts_open_ms` may reference only
  data with `ts_close_ms <= ts_open_ms`. Implemented by always
  shifting features by one bar before joining onto events.
- Forward outcomes anchored on the bar that closes strictly
  **after** the event bar.
- Funding rate forward-filled forward in time only, never
  back-filled.
- OI / mark / index ffilled with explicit TTL; samples older than
  TTL are NaN, not stale-filled.
- Predicted funding rate stored in a separate column from realized
  funding rate to prevent silent overlap.
- All storage and computation in UTC; conversion to local sessions
  is a derived feature.
- Universe is BTCUSDT + ETHUSDT only in v1; documented in
  `universe.yaml` so future expansion does not silently change
  historical regime stats.
- Re-write semantics: every processed parquet is rebuilt in full
  from raw on schema or feature definition change. Old files are
  versioned `<name>.v<n>.parquet` for one cycle then garbage-
  collected by `rebuild.py --gc`.
- Quality gating: a (date, series) with `failed_schema` or
  `received_bars < 0.99 * expected_bars` is excluded from
  `processed/` and surfaced as red in the markdown roll-up.
- Rate limits: documented Binance fapi weight limits respected;
  ingest paces requests via `sources.yaml`. Retries: exponential
  backoff with jitter, max 5 retries, then mark partial.
- API drift: each ingestor stores the API URL and a hash of the
  response keys it accepts; on mismatch the run is marked
  `schema_drift` and is not promoted.
- Hypothesis-revival risk: seed briefs (Phase 6) must include the
  rejected-mechanism distinctness check from `.codex/AGENTS.md`
  Section 10 so the leaderboard does not silently re-propose
  H0001..H0007.
- Verdict-leak risk: nothing in the Data Layer ever writes to
  `experiments_log.md`, `results/experiments.csv`, or any
  `obsidian/05_Rejected/` or `obsidian/06_Passed/` file.
- License: only documented public endpoints; module headers cite
  the doc URL. No scraping of authenticated dashboards.
- Security: no API key in v1; if added later for higher rate
  limits, it goes through repo secrets, never a committed file.
- Cost: storage budget for v1 (BTCUSDT + ETHUSDT, two timeframes,
  Binance only, 12 months of derivatives) documented in
  `data_layer/README.md`.

## 14. What requires user approval before implementation

Each item below is a separate go / no-go decision and a separate
PR. Plan-only PR (this PR) does not need approval.

- A. Phase 1 scaffold (file-only).
- B. Phase 2 Binance smoke ingest (new Python deps; first network
  call).
- C. Phase 3 Binance derivatives + features + regimes (CPU work +
  larger Parquet).
- D. Phase 4 events + outcomes + leaderboard (defines what counts
  as an event for hypothesis generation; user must agree to the
  definitions in Sections 6 and 7).
- E. Phase 5 cross-exchange mirrors are deferred / out of scope unless
  the user explicitly re-approves Bybit or OKX later.
- F. Phase 6 hypothesis seed briefs (touches
  `obsidian/00_INGEST_LOG.md` via a single append per run;
  otherwise wiki untouched).
- G. Phase 7 liquidations + order book (large data; explicit
  opt-in only).
- H. Any change to the rejected-mechanism distinctness check in
  seed briefs (interacts with `.codex/AGENTS.md` Section 10 and
  could be misused to revive a rejected hypothesis).

Out of scope without separate approval: any change to `.codex/`,
`MASTER_CONTEXT.md`, `PROJECT_INSTRUCTIONS.md`, top-level
`README.md`, `experiments_log.md`, `results/experiments.csv`, or
`obsidian/01_Rules/` through `obsidian/10_Codex_Instructions/`. The
Data Layer is a sibling of these, not a replacement.

End of plan.
