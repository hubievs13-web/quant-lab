# Data Layer

File-based Market Research Data Layer for crypto futures research.

Plan: `data_layer/DATA_LAYER_IMPLEMENTATION_PLAN.md` (Sections 1-14).
Current phase: **Phase 1 (scaffold only)**. Phases 2-7 are gated by
user approval per plan Section 14.

## What is in this folder

- `config/` - symbols, sources, features, regime/event thresholds.
- `ingest/` - per-exchange ingest modules (Phase 2+; stubs only).
- `process/` - feature / regime / event / outcome / leaderboard /
  quality engines (Phase 2+; stubs only).
- `scripts/` - `cli.py` plus stub fetch / rebuild / refresh
  scripts. All Phase 1 stubs print "not implemented".
- `reports/` - Codex-readable markdown only. <= 5 KB per file.
- `store/` - bulk Parquet (gitignored, do-not-read-by-default).

## CLI

    python -m data_layer.scripts.cli --help

All subcommands print "not implemented" until their phase is
approved.

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

## Out of scope without separate approval

- `.codex/`, `MASTER_CONTEXT.md`, `PROJECT_INSTRUCTIONS.md`,
  top-level `README.md`, `experiments_log.md`,
  `results/experiments.csv`, `obsidian/01_Rules/` through
  `obsidian/10_Codex_Instructions/`.
- Any new Python dependency.
- Any network call (none until Phase 2).
