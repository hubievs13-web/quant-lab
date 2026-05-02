# MASTER_CONTEXT - Quant Lab

Last updated: 2026-05-02

## 1. Mission

Find crypto futures strategies for QuantConnect using strict falsification.

Business target:
+5% net/day on small capital.

Important:
+5% net/day is NOT a validation criterion. A strategy is valid only if it passes the falsification framework.

## 2. Operating model

Actors:

1. User:
- runs Codex;
- manually pastes main.py into QuantConnect;
- manually runs backtests;
- downloads artifacts;
- sends screenshots/logs/files to ChatGPT.

2. Codex:
- researcher: creates candidate edges and hypothesis notes;
- engineer: creates QuantConnect strategy package;
- auditor: records rejected/passed outcome and post-mortem;
- updates MASTER_CONTEXT.md after major events;
- does NOT run QuantConnect;
- does NOT decide final verdict;
- does NOT tune failed strategies.

3. ChatGPT:
- reviews hypotheses before engineer mode;
- reviews code before smoke test;
- reviews smoke test;
- applies falsification framework after full backtest;
- gives Codex prompts;
- forbids tuning failed strategies.

## 3. Local project path

C:\Users\эззизз\Desktop\vscode\quant-lab\

Obsidian vault:
C:\Users\эззизз\Desktop\vscode\quant-lab\obsidian

QuantConnect project:
30774195

Lean Engine:
v17685

## 4. Hard rules

1. Never tune parameters after failed backtest.
2. Never claim PASS without all falsification criteria.
3. Monte Carlo runs only after criteria 1-6 preliminary pass.
4. Free parameters <= 3 per hypothesis.
5. Fee/slippage assumption:
   - Binance futures taker fee 0.04% per side;
   - total round-trip friction around 0.18%.
6. Pre-fee edge floor >= 0.10% per trade.
7. No data leakage:
   - no future bars;
   - no same-bar close signal with same-close execution;
   - next-bar execution required;
   - multi-asset timestamps must be aligned.
8. Screenshots are secondary evidence.
9. CSV/logs/statistics are primary evidence.
10. If only screenshots exist, evidence confidence is LOW_CONFIDENCE.
11. Verdict only PASS / FAIL / INCONCLUSIVE.

## 5. Falsification framework v3

A hypothesis FAILS if any required criterion fails.

Criteria:

1. Trade count:
   - intraday/high-frequency: >= 300 completed trades;
   - swing: >= 30 completed trades.

2. OOS Sharpe > 1.0.

3. OOS net average trade > 0.

4. Max Drawdown < 25%.

5. Pre-fee average trade >= 0.10% per trade.

6. Either:
   - Win Rate >= 50% IS and OOS;
   OR
   - Profit Factor >= 1.25 with stable payoff ratio.

7. Monte Carlo only after criteria 1-6 pass:
   - 1000 sims minimum;
   - P5(final equity) > starting capital;
   - P95(max drawdown) < 25%;
   - probability(final equity < starting capital) < 5%.

## 6. Current rejected hypotheses

- H0001: ETH spread reclaim mean reversion, 1m spot, rejected.
- H0002: BTCUSDT -> ETHUSDT 5m perp lead-lag, rejected.
- H0003: SOL liquidation wick recovery, 5m spot, rejected.
- H0004: BTC microtrend trailing, 1m spot, rejected.
- H0005: Smooth Blue Jellyfish / simple same-symbol 5m perp compression breakout, BTCUSDT/ETHUSDT, rejected.
- H0006: BTC Bollinger Band rejection MR + range filter, 5m spot, rejected.
- H0007: funding-settlement unwind, 5m BTCUSDT/ETHUSDT Binance USD-M Futures, rejected.

## 7. Latest result - H0007 final result

Hypothesis:
H0007_funding_settlement_unwind

Strategy:
S0007_funding_settlement_unwind

Backtest:
Determined Orange Mule

Period:
2024-01-01 to 2025-01-01

Metrics:
- Start Equity: 200.00 USDT
- End Equity: 102.62 USDT
- Net Profit: -48.692%
- Sharpe: -5.112
- Drawdown: 48.900%
- Win Rate: 32%
- Completed trades: approximately 509
- Total Orders: 1018
- Total Fees: 48.32 USDT
- Profit Factor / Profit-Loss Ratio: 0.73
- Expectancy: -0.450
- Average pre-fee trade: -0.0802%
- Average post-fee trade: -0.1602%

Verdict:
FAIL / REJECTED

Monte Carlo:
Not run because criteria 1-6 failed.

Failed criteria:
- Trade count: passed, 509 >= 300.
- Sharpe: failed, -5.112.
- Net avg trade: failed, average post-fee trade -0.1602%.
- Drawdown: failed, 48.900%.
- Pre-fee avg: failed, -0.0802%.
- WR/PF: failed, win rate 32% and PF 0.73.
- MC: not allowed.

Technical notes:
- H0007 compiled and ran.
- BTCUSDT and ETHUSDT loaded as CryptoFuture.
- SIGNAL, ENTRY, TRADE, and EXIT_ORDER_SUBMITTED logs existed.
- Sampled logs showed no same-bar execution; execution_bar_time was later than signal_bar_time.
- Failure is research/mechanism failure, not technical smoke-test failure.

Lesson:
Scheduled Binance USD-M funding-settlement timing plus bar-only pre-settlement displacement did not produce a standalone intraday edge. The funding clock alone is insufficient without confirmed derivatives state variables such as actual funding regime, basis/premium, or OI.

Forbidden follow-ups:
- Do not tune H0007 parameters.
- Do not rerun H0007 with a different settlement window, displacement threshold, or hold bars.
- Do not add stop-loss, take-profit, trailing stop, cooldown, volatility filter, trend filter, leverage changes, or sizing changes to rescue H0007.
- Do not rebrand scheduled funding-settlement bar-only unwind as a new hypothesis.

Status:
Closed.

## 8. Key lessons

- L0001: Plain-vanilla <=5m spot mean-reversion and microtrend patterns on BTC/ETH/SOL did not survive costs.
- L0002: Simple BTCUSDT -> ETHUSDT 5m perpetual lead-lag without independent regime logic failed and must not be repeated.
- L0005: Simple same-symbol 5m Binance USD-M futures compression breakout failed badly after realistic friction.
- L0006: Scheduled funding-settlement timing plus bar-only pre-settlement displacement failed as a standalone BTCUSDT/ETHUSDT Binance USD-M intraday edge.

## 9. Current status

Current phase:
Engineer package created for H0008.

Next task:
ChatGPT code review for `strategies/H0008_funding_premium_crowding_unwind/main.py`, supporting README/diagnostics, and `obsidian/03_Strategies/S0008_funding_premium_crowding_unwind.md`.

Active hypothesis:
H0008_funding_premium_crowding_unwind.

Previous researcher cycle:
2026-05-01: Created CE0016-CE0020 as candidate edges. CE0016 predicted funding flip repricing, CE0017 OI-price absorption reversal, CE0018 mark-last stop-trigger dislocation, and CE0019 taker-flow imbalance aftershock are BLOCKED because required funding/OI/mark/signed-flow data is not confirmed as native in QC Lean v17685 for Binance USD-M Futures. CE0020 perp volume dominance rotation is researcher-rejected because expected pre-fee edge is not honestly above 0.10% and it risks becoming disguised short-horizon momentum. Zero selected hypotheses.

Current blocker:
No active data-access blocker for H0008 engineering review using audited TIER 1 data. Backtests, strategy PASS claims, profitability claims, parameter tuning, and QuantConnect production custom-data assumptions remain unauthorized until separately approved and reviewed.

Latest infrastructure note:
2026-05-01: Created `obsidian/08_Data_Notes/DL0001_derivatives_data_layer_proposal.md`. It recommends a proposal-only Phase 2 local derivatives data layer for BTCUSDT and ETHUSDT, with no ingestion implementation and no trading hypothesis yet.

Phase 2 inventory status:
DL0001 was approved for inventory planning only. Created `obsidian/08_Data_Notes/DL0002_binance_um_data_inventory_plan.md` as a plan to verify Binance USD-M BTCUSDT/ETHUSDT dataset availability. No data folder, ingestion, backtest, strategy code, QC custom data, or H0008 is authorized yet.

Latest inventory verification:
DL0002 was approved for minimal inventory verification implementation. Created `scripts/verify_binance_um_inventory.py` and metadata-only outputs under `data_inventory/`: `source_inventory.csv`, `gaps_report.csv`, and `checksums.csv`. Created `obsidian/08_Data_Notes/DL0003_binance_um_inventory_results.md`. No full historical datasets were downloaded. No strategy, backtest, QC custom data, feature engineering, parameter search, or H0008 was created.

DL0003 result:
Only `index_price_klines` verified as TIER 1 for both BTCUSDT and ETHUSDT in this run. Several likely-free datasets remained UNKNOWN because Binance REST/archive checks had SSL handshake timeouts. OI and basis are recent-only / TIER 2 class; taker buy/sell volume remains expected recent-only but was not cleanly verified due request errors. Free-only Phase 2 is not yet enough to support H0008.

DL0004 result:
Ran a narrower archive-first rerun for likely TIER 1 datasets only. Created `scripts/verify_binance_um_archive_first.py` plus `data_inventory/source_inventory_archive_first.csv`, `gaps_report_archive_first.csv`, and `checksums_archive_first.csv`. Created `obsidian/08_Data_Notes/DL0004_archive_first_inventory_results.md`. Verified `um_klines_1m`, `funding_rate_history`, `premium_index_klines`, `mark_price_klines`, and `index_price_klines` as TIER 1 for both BTCUSDT and ETHUSDT using 2021/2024 archive evidence, 2024 sample schema/timestamps, checksums, and latest REST fallback. Latest monthly archive was NOT_FOUND for kline-like datasets, so later ingestion should use REST fallback for the newest not-yet-archived period.

Current data status:
DL0005 result:
Created `scripts/ingest_binance_um_tier1.py` and normalized raw TIER 1 files under `data/raw/binance_um/`, with `data/manifests/tier1_manifest.csv`, `data/manifests/tier1_checksums.csv`, `data/reports/tier1_gaps_report.csv`, and `data/reports/tier1_ingestion_errors.csv`. Ingested BTCUSDT/ETHUSDT from `2024-01-01T00:00:00Z` to `2026-05-02T07:19:00Z` for `um_klines_1m`, `funding_rate_history`, `premium_index_klines`, `mark_price_klines`, and `index_price_klines`. Manifest rows: 290; OK: 284; INTEGRITY_FAIL: 6; request errors: 0; duplicate rows: 0; non-monotonic rows: 0; checksum rows: 290. Total compressed normalized bytes: 287,451,246.

DL0005 strict ingestion status before policy:
PARTIAL / STRICT FAIL. Missing rows: total 12 across `premium_index_klines`, `mark_price_klines`, and `index_price_klines` for BTCUSDT and ETHUSDT in 2024-08. Each affected file is missing `2024-08-12T10:02:00Z` and `2024-08-12T10:03:00Z`.

H0008 remains not created. No strategy, backtest, feature engineering, parameter search, or QC custom data is authorized.

DL0006 result:
Created `scripts/resolve_tier1_price_state_gaps.py` and `data/reports/tier1_gap_resolution_report.csv`. Targeted only the 12 exact missing rows across `premium_index_klines`, `mark_price_klines`, and `index_price_klines` for BTCUSDT/ETHUSDT at `2024-08-12T10:02:00Z` and `2024-08-12T10:03:00Z`. Binance REST source status was OK for all 12 target checks, but recovered rows: 0; inserted rows: 0; validation status: NOT_RETURNED for all 12. Normalized raw data files were not modified. Manifest remains OK: 284, INTEGRITY_FAIL: 6; total missing rows: 12; duplicate rows: 0; non-monotonic timestamp rows: 0; request errors: 0.

Updated ingestion integrity status:
PARTIAL after DL0006, then accepted under DL0007 with a known no-fill/no-signal exception for the exact unresolved 12 price-state observations.

DL0007 result:
Created `obsidian/08_Data_Notes/DL0007_no_fill_no_signal_gap_policy.md`. The policy approves no-fill/no-signal handling only for `premium_index_klines`, `mark_price_klines`, and `index_price_klines` on BTCUSDT/ETHUSDT at `2024-08-12T10:02:00Z` and `2024-08-12T10:03:00Z`. No rows may be synthesized, interpolated, forward-filled, backfilled, inferred from neighboring data, or reconstructed from future data. Future feature tables must mark these timestamps as unavailable, and research/strategy logic must skip signal generation at these timestamps and any dependent 5m bar if source completeness is required.

TIER 1 ingestion status:
Accepted with known no-fill/no-signal exception. Point-in-time feature audit may now be requested. H0008 remains not created.

DL0008 result:
Created `scripts/audit_point_in_time_tier1.py` plus `data/reports/point_in_time_audit_summary.csv`, `point_in_time_availability_flags.csv`, `point_in_time_5m_dependency_audit.csv`, and `point_in_time_audit_errors.csv`. Created `obsidian/08_Data_Notes/DL0008_point_in_time_audit_results.md`. Audit summary rows: 34; PASS checks: 34; failed checks: 0; audit errors: 0; availability rows: 2,454,640; 5m dependency rows: 490,928. DL0007 gaps remain unfilled and are flagged unavailable/no-signal. The dependent 5m bar starting `2024-08-12T10:00:00Z` is flagged no-signal for both BTCUSDT and ETHUSDT when complete 1m price-state source data is required. Funding availability uses only `funding_timestamp <= audit_timestamp`; no funding value is used before timestamp. No future transforms, OOS normalization, signals, features, strategy code, backtests, QC custom data, or parameter search were created.

Point-in-time audit status:
PASS. Data is ready for a researcher cycle using only audited TIER 1 data and the DL0007 no-fill/no-signal exception. H0008 remains not created unless explicitly approved later.

Latest researcher cycle:
Created candidate edge notes `CE0021_funding_premium_crowding_unwind`, `CE0022_mark_last_dislocation_snapback`, `CE0023_premium_compression_repricing`, `CE0024_derived_basis_extension_snapback`, and `CE0025_mark_premium_divergence_continuation` under `obsidian/08_Data_Notes/`. Ranked CE0021 highest because it combines actual settled funding regime with premium-index compression, uses only audited TIER 1 data, has a plausible a priori pre-fee edge of 0.12-0.18 percent, and is distinct from H0007 clock-only funding unwind.

H0008 result:
Created `obsidian/02_Hypotheses/H0008_funding_premium_crowding_unwind.md`. Mechanism: persistent settled funding regime identifies crowded leveraged side; premium-index compression against that crowded side confirms possible unwind. Symbols BTCUSDT/ETHUSDT, completed 5m decision bars from audited 1m TIER 1 data. Datasets: `um_klines_1m`, `funding_rate_history`, `premium_index_klines`; optional sanity only from `mark_price_klines` and `index_price_klines`. Free parameters: `funding_regime_abs_threshold`, `premium_compression_pct`, `hold_bars` (3 total). Expected combined frequency: 5-12 trades/day. DL0007 no-fill/no-signal policy applies. No strategy code, backtest, QC custom data, feature production, or parameter search was created.

S0008 engineering package result:
Created `strategies/H0008_funding_premium_crowding_unwind/main.py`, `README.md`, `diagnostics.md`, and `obsidian/03_Strategies/S0008_funding_premium_crowding_unwind.md`. Package implements H0008 in single-file QuantConnect Lean Python with BTCUSDT/ETHUSDT only, completed 5m decision bars, next-bar execution, funding values only after funding timestamp, DL0007 missing timestamps and dependent 5m bars as no-signal, exactly three H0008 free parameters, Binance futures taker fee model at 0.04 percent per side, explicit slippage buffer assumptions, one open position per symbol, fixed fractional sizing, 2x leverage, and 20 percent project drawdown stop. H0008 requires custom funding and premium-index CSV streams; QuantConnect native availability is not assumed. No backtest was run. No strategy PASS, profitability claim, parameter search, or production custom-data validation was created.

Allowed next directions:
- Send S0008/H0008 engineering package to ChatGPT for code review.
- If accepted by code review, next separately approved step may be QuantConnect smoke-test setup with custom data path verification; do not run a full backtest before that approval.
- Future candidate families partially enabled after gap resolution: premium compression repricing, mark-last dislocation, funding regime reversal with premium confirmation, derived basis using perp last price and index price.
- Still blocked: OI absorption, taker-flow imbalance, liquidation-based hypotheses.
- If OI/taker/basis mechanisms remain priority, decide on paid vendor, forward collection, or a separately approved raw-trade reconstruction plan.
- A futures-specific mechanism not based on bar-only timing, bar-only compression, BTC-to-ETH lead-lag, generic 1m/5m price-pattern MR/momentum, or ordinary unsigned volume.
- Phase 2 data-layer proposal for funding/OI/basis may be considered only if explicitly requested by the user.

Avoid:
- simple BTC->ETH 5m lead-lag;
- same H0002 mechanism with changed thresholds;
- simple 1m/5m price-pattern MR/momentum;
- simple same-symbol 5m compression breakout;
- scheduled funding-settlement bar-only unwind;
- unavailable data unless clearly marked BLOCKED;
- any H0001-H0007 mechanism with different parameters or added filters.

## 10. Standard workflow

1. Codex researcher -> candidate edges + hypothesis.
2. ChatGPT reviews hypothesis.
3. If accepted, Codex engineer -> main.py + README + diagnostics.
4. ChatGPT reviews code.
5. User runs 3-7 day smoke test in QuantConnect.
6. ChatGPT reviews smoke test.
7. If technically passed, user runs full backtest.
8. ChatGPT applies falsification framework.
9. If FAIL, Codex auditor closes hypothesis.
10. Codex updates MASTER_CONTEXT.md.
11. User uploads/replaces updated MASTER_CONTEXT.md in ChatGPT Project.
12. No tuning failed strategy.

## 11. MASTER_CONTEXT maintenance

MASTER_CONTEXT.md must be updated by Codex after each major research-cycle event.

The user should not manually rewrite this file unless necessary.

After Codex updates MASTER_CONTEXT.md, the user must upload/replace the updated file in the ChatGPT Project files.

Codex update protocol:
MASTER_CONTEXT_UPDATE_PROTOCOL.md
