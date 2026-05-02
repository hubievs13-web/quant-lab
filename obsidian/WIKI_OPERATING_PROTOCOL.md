# WIKI_OPERATING_PROTOCOL

Constitution for the LLM Wiki layer inside `obsidian/`. Codex must
read this file before any wiki write.

If this protocol conflicts with `.codex/AGENTS.md`, AGENTS.md wins.
This file does not change any hard rule, falsification framework
item, fee model, rejected mechanism table, or verdict authority.

## 1. Purpose

The wiki layer reduces token usage and prevents repeated mistakes.
It does NOT replace the canonical research pipeline:

idea -> hypothesis -> evidence -> pre-backtest gates -> code -> smoke
test -> full backtest -> Monte Carlo -> verdict.

The wiki only adds: a stable entry point, a hot-state cache, a
navigation map, an ingest log, a lint report, summaries, decision
pages, and a QC-Lean error library.

## 2. Read order (mandatory)

1. `obsidian/00_START_HERE.md`
2. `obsidian/00_HOT.md`
3. `obsidian/00_INDEX.md` (only if navigation needed; until Step 5 of
   the migration is approved, fall back to `obsidian/00_Index.md`)
4. Targeted linked files only.

`MASTER_CONTEXT.md` and `PROJECT_INSTRUCTIONS.md` are read on demand,
not by default.

## 3. Token budgets (defaults)

- `00_START_HERE.md`: ~80 lines max.
- `00_HOT.md`: ~40 lines max.
- `00_INDEX.md`: ~120 lines max.
- Each `obsidian/wiki/*` note: ~150 lines target, ~300 lines hard cap.
- Each `obsidian/wiki/qc_lean/errors/*` note: ~80 lines target.

If a note grows past its cap, split it; do not let it bloat.

## 4. File-size and scan rules

1. Never scan the whole repository by default.
2. Never read any file larger than 5 MB without explicit user
   approval. This is a hard rule.
3. Prefer files smaller than 200 KB. Above 200 KB, prefer the matching
   summary in `obsidian/wiki/summaries/`.
4. Do not open by default:
   - `results/raw/`, `results/trades/`, `results/orders/`,
     `results/logs/`, `results/reports/`.
   - `results/experiments.csv` beyond the latest relevant row.
   - `obsidian/04_Backtests/**/statistics.json`,
     `obsidian/04_Backtests/**/*_logs.txt`, and any file in
     `obsidian/04_Backtests/` larger than 200 KB other than
     `report.md`.
   - `obsidian/raw/` (always read the matching summary instead).
   - Strategy `main.py` files for hypotheses other than the one being
     worked on.
5. Known oversize artifact:
   `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/statistics.json`
   ~2.9 MB. Do not read directly.

## 5. Writes (what the wiki may and may not do)

The wiki layer MAY:

- Create / update its own files under `obsidian/00_*`,
  `obsidian/WIKI_OPERATING_PROTOCOL.md`, `obsidian/wiki/`,
  `obsidian/raw/`, `obsidian/templates/`.
- Append to `obsidian/00_INGEST_LOG.md` (one line per action).
- Regenerate `obsidian/00_LINT_REPORT.md`, moving the previous
  snapshot to `obsidian/wiki/lint_history/`.

The wiki layer MUST NOT:

- Edit `.codex/AGENTS.md`, `MASTER_CONTEXT.md`,
  `PROJECT_INSTRUCTIONS.md`, `README.md`,
  `MASTER_CONTEXT_UPDATE_PROTOCOL.md`, `experiments_log.md`, or
  `results/experiments.csv` from inside this protocol. Edits to these
  files happen only via approved migration steps from
  `PLAN_LLM_WIKI_MIGRATION.md`.
- Edit any file under `obsidian/01_Rules/`, `obsidian/02_Hypotheses/`,
  `obsidian/03_Strategies/`, `obsidian/04_Backtests/`,
  `obsidian/05_Rejected/`, `obsidian/06_Passed/`,
  `obsidian/07_Lessons/`, `obsidian/08_Data_Notes/`,
  `obsidian/09_Daily_Logs/`, `obsidian/10_Codex_Instructions/`.
- Edit anything under `strategies/`, `scripts/`, `research/`, or
  `results/`.
- Delete any file. Files are moved, never removed.

## 6. Status protection (active / rejected / passed)

Status truth lives in the canonical store:

- Active:   `obsidian/02_Hypotheses/Hxxxx_*.md`.
- Rejected: `obsidian/05_Rejected/Hxxxx_*.md` (or
  `pre_backtest_rejected/`).
- Passed:   `obsidian/06_Passed/Hxxxx_*.md`.

Wiki decision pages (`obsidian/wiki/decisions/Hxxxx.md`) are
read-only mirrors. They derive status from path; they never set it.

If a wiki decision page disagrees with the canonical store, the
canonical store wins. The wiki page is regenerated, never edited to
override truth.

A rejected hypothesis stays rejected. To revive an idea, the
researcher must:

1. Cite new external evidence.
2. File a new hypothesis with a distinct mechanism.
3. Pass the existing pre-backtest auditor flow.

The wiki must not lower this bar.

## 7. Verdict handling

- Codex never issues a verdict. The external Devin chat owns
  PASS / FAIL / INCONCLUSIVE / PRELIMINARY_PASS / FINAL_PASS.
- Wiki notes never restate or modify a verdict.
- A wiki summary may quote the verdict text and link to the
  authoritative file. It must not paraphrase in a way that softens or
  hardens the verdict.
- `experiments_log.md` is the append-only verdict log. The wiki
  reads it, never writes to it.

## 8. QuantConnect / Lean error handling

Layout:

```
obsidian/wiki/qc_lean/
  errors/    one note per recurring error (QCERR-xxxx_<slug>.md)
  patterns/  one note per recurring pattern / fix recipe
```

Workflow when an error is encountered:

1. Search `obsidian/wiki/qc_lean/errors/` by symptom (exact log
   substring if possible).
2. If found: apply the recorded fix. Add a new "occurrence" line at
   the bottom of the note (date, backtest ID, hypothesis ID).
3. If not found: create `QCERR-xxxx_<slug>.md` from
   `obsidian/templates/_TEMPLATE_qc_lean_error.md`. Status: `open`.
4. When the user confirms a fix worked, append a "Resolution"
   section. Do not edit prior content. Status flips to `resolved`.
5. Cross-link the relevant pattern note in
   `obsidian/wiki/qc_lean/patterns/` if applicable.

This library does not authorize tuning. AGENTS.md section 5 rule 1
(no parameter tuning after a failed backtest) still wins.

## 9. Append-only logs

The following files are append-only:

- `obsidian/00_INGEST_LOG.md`
- `experiments_log.md`
- Per-occurrence sections inside any
  `obsidian/wiki/qc_lean/errors/QCERR-*.md`.

`obsidian/00_LINT_REPORT.md` is overwritten as a snapshot, but the
prior snapshot is preserved by moving it to
`obsidian/wiki/lint_history/` first.

## 10. Failure modes the protocol must prevent

1. Reviving a rejected hypothesis without new evidence.
2. Reading a 200 MB JSON / CSV by accident.
3. Treating screenshots as PRIMARY evidence (they are SECONDARY; see
   `.codex/README.md`).
4. Producing a wiki summary that contradicts the canonical file.
5. Editing AGENTS.md / MASTER_CONTEXT.md / role files from inside the
   wiki workflow. Those edits go through migration steps, not wiki
   ingest.
6. Re-deriving the same QC-Lean error fix from scratch.
7. Long agent answers that repeat known background context.

If any of the above occurs, stop, log it in
`obsidian/00_LINT_REPORT.md`, and ask the user.

## 11. Versioning

This protocol is versioned by Git history of this file. Material
changes (anything beyond typo fixes) require a separate migration
plan note, mirroring the format of
`PLAN_LLM_WIKI_MIGRATION.md`.
