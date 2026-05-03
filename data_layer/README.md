# Data Layer

File-based Market Research Data Layer for crypto futures research.

Plan: `data_layer/DATA_LAYER_IMPLEMENTATION_PLAN.md` (Sections 1-14).
Current phase: **Phase 2 (Binance smoke ingest)**. Phases 3-4 and 6-7 are
still gated by user approval per plan Section 14.

Phase 2 source: `data.binance.vision` public CDN (no API key).
Live Binance fapi REST is geoblocked from many cloud regions; the
documented public archive is the v1 fallback used by all Phase 2
fetchers.

## What is in this folder

- `config/` - symbols, sources, features, regime/event thresholds.
- `ingest/` - Binance ingest modules. Binance OHLCV / funding /
  open-interest implemented in Phase 2; Bybit and OKX are deferred
  out of scope unless the user explicitly re-approves them later.
- `process/` - feature / regime / event / outcome / leaderboard /
  quality engines. `align`, `join`, `quality` implemented in Phase 2;
  the rest are stubs until Phases 3-4.
- `scripts/` - `cli.py` plus fetch / rebuild / refresh scripts.
  Phase 2 wires `fetch-binance-smoke`, `rebuild-smoke`,
  `quality-smoke`, `refresh-summaries`.
- `reports/` - Codex-readable markdown only. <= 5 KB per file.
- `store/` - bulk Parquet (gitignored, do-not-read-by-default).

## CLI

    python -m data_layer.scripts.cli --help
    python -m data_layer.scripts.cli fetch-binance-smoke
    python -m data_layer.scripts.cli rebuild-smoke
    python -m data_layer.scripts.cli quality-smoke
    python -m data_layer.scripts.cli refresh-summaries

Future-phase subcommands still print "not implemented".

## Codex / Devin read order

For any Data Layer question, read in this order and stop as soon as
the answer is found:

1. `data_layer/reports/summaries/universe_status.md`
2. `data_layer/reports/summaries/regime_summary.md`
3. `data_layer/reports/summaries/event_catalog.md`
4. `data_layer/reports/summaries/feature_catalog.md`
5. `data_layer/reports/leaderboards/latest_event_leaderboard.md`
6. `data_layer/reports/quality/latest_summary.md`
7. `data_layer/reports/summaries/hypothesis_seed_briefs/<topic>.md`

Forbidden by default:

- `data_layer/store/**` (raw / processed Parquet).
- Any file > 5 MB.

## Report / brief size policy

- All Codex-readable markdown reports: max 5 KB.
- Hypothesis seed briefs (Phase 6): max 80 lines AND max 5 KB.
- Caps live in `data_layer/config/events.yaml -> report_caps`.

## Runtime dependencies (Phase 2)

- `pandas`, `pyarrow` (Parquet I/O, joins, dedup, asof merges).
  Install: `pip install pandas pyarrow`.
- HTTP via `urllib` (stdlib); no `requests` dependency.

## Out of scope without separate approval

- `.codex/`, `MASTER_CONTEXT.md`, `PROJECT_INSTRUCTIONS.md`,
  top-level `README.md`, `experiments_log.md`,
  `results/experiments.csv`, `obsidian/01_Rules/` through
  `obsidian/10_Codex_Instructions/`.
- New Python dependencies beyond `pandas` / `pyarrow`.
- Bybit / OKX ingest; deferred out of scope unless explicitly
  re-approved later.
- Features / regimes / events (Phases 3-4).

## Next Data Layer step

- Validate ETHUSDT on Binance using the existing Data Layer path. Do
  not ingest or create data until the user approves that run.
