# 00_START_HERE

First file every agent (Codex / Devin) reads in this repository.

This file is intentionally short. If you read further than this page
without a reason, you are wasting tokens.

## Read order

1. This file: `obsidian/00_START_HERE.md`.
2. Hot state: `obsidian/00_HOT.md`.
3. Navigation map: `obsidian/00_INDEX.md` (only if you need to find
   something).
4. Wiki rules: `obsidian/WIKI_OPERATING_PROTOCOL.md`.
5. Targeted linked files only.

Read `MASTER_CONTEXT.md` only when full project handoff context is
needed. Read `PROJECT_INSTRUCTIONS.md` only when project-level
operating rules are needed. Do not load them by default.

## Default mode

LOW TOKEN MODE is on by default. Canonical text lives in
`obsidian/WIKI_OPERATING_PROTOCOL.md`. Summary:

- Default response style: short, direct, no motivational text.
- Do not scan the whole repository.
- Do not read files larger than 5 MB. Ever, without explicit user
  approval.
- Prefer summaries in `obsidian/wiki/` over raw files.
- Do not open `results/raw/`, large backtest artifacts, or
  `obsidian/raw/` by default.
- Append logs only. Never overwrite history.
- Output: what I checked, what I changed or propose to change, exact
  next step. No long theory unless requested.

## Pipeline (preserved as-is)

idea -> hypothesis -> evidence -> pre-backtest gates -> code -> smoke
test -> full backtest -> Monte Carlo -> verdict.

This wiki layer does not replace the pipeline. It only makes
navigation cheaper.

## Verdict authority (do not violate)

- Codex never issues a verdict.
- The external Devin chat owns PASS / FAIL / INCONCLUSIVE per the
  Falsification Framework V3.
- Wiki notes never restate or change a verdict. They only point at
  the canonical file.

## Status of files in this folder

- `00_START_HERE.md`  this file. First read.
- `00_HOT.md`         shortest current project state. Second read.
- `00_INDEX.md`       navigation map (created by Step 5 of the
  migration; until then use the existing `obsidian/00_Index.md`).
- `00_INGEST_LOG.md`  append-only log of sources ingested into the
  wiki.
- `00_LINT_REPORT.md` wiki health snapshot. Generated on demand.
- `WIKI_OPERATING_PROTOCOL.md` wiki rules / token budgets / verdict
  handling / QC-Lean error handling.
- `wiki/`             compact processed knowledge notes.
- `raw/`              unprocessed sources. Never read by default.
- `templates/`        wiki-only templates.

If you need a hypothesis, a backtest, a strategy, or a lesson, do not
search this folder for it. Use the canonical store:

- Active hypotheses:  `obsidian/02_Hypotheses/`
- Strategies (notes): `obsidian/03_Strategies/`
- Backtests:          `obsidian/04_Backtests/`
- Rejected:           `obsidian/05_Rejected/`
- Passed:             `obsidian/06_Passed/`
- Lessons:            `obsidian/07_Lessons/`
- Data notes:         `obsidian/08_Data_Notes/`
- Daily logs:         `obsidian/09_Daily_Logs/`
- Codex prompts:      `obsidian/10_Codex_Instructions/`

## Next action for the agent

Stop here unless your task explicitly requires more. Read
`obsidian/00_HOT.md` next.
