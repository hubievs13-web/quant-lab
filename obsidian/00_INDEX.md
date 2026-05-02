# 00_INDEX

Navigation map of the Obsidian vault. Read this only when you need
to find something. Otherwise stop after `00_HOT.md`.

This file replaces `00_Index.md` (case-aware Git rename, Step 5 of
the LLM Wiki migration). Original content is preserved verbatim
below the separator.

Hard cap: ~120 lines.

## Wiki layer entry points

- `obsidian/00_START_HERE.md` — first read every session.
- `obsidian/00_HOT.md` — shortest current state.
- `obsidian/WIKI_OPERATING_PROTOCOL.md` — wiki rules, token budgets,
  verdict handling, QC / Lean error workflow.
- `obsidian/00_INGEST_LOG.md` — append-only ingest log.
- `obsidian/00_LINT_REPORT.md` — wiki health snapshot (on demand).
- `obsidian/wiki/` — compact processed knowledge notes.
- `obsidian/raw/` — unprocessed sources, never read by default.
- `obsidian/templates/` — wiki-only templates.

## Quick paths by task

- Current project state -> `obsidian/00_HOT.md`.
- Full handoff context -> `MASTER_CONTEXT.md` (only when needed).
- Project-level rules -> `PROJECT_INSTRUCTIONS.md` (only when needed).
- Agent operating rules -> `.codex/AGENTS.md` and `obsidian/01_Rules/`.
- Researcher mode -> `.codex/roles/researcher.md` +
  `obsidian/10_Codex_Instructions/researcher_prompt.md`.
- Engineer mode -> `.codex/roles/engineer.md` +
  `obsidian/10_Codex_Instructions/engineer_prompt.md`.
- Auditor mode -> `.codex/roles/auditor.md` +
  `obsidian/10_Codex_Instructions/auditor_prompt.md`.

## Quick paths by artifact

- Active hypotheses -> `obsidian/02_Hypotheses/`.
- Strategy cross-ref notes -> `obsidian/03_Strategies/`.
- Strategy code -> `strategies/Hxxxx_<slug>/`.
- Backtest reports -> `obsidian/04_Backtests/<BTID>_<HID>_<DATE>/report.md`
  (do not open the matching `statistics.json` or `*_logs.txt`).
- Rejected -> `obsidian/05_Rejected/`.
- Pre-backtest rejected -> `obsidian/05_Rejected/pre_backtest_rejected/`.
- Passed -> `obsidian/06_Passed/`.
- Lessons -> `obsidian/07_Lessons/`.
- Candidate edges + data availability -> `obsidian/08_Data_Notes/`.
- Daily logs -> `obsidian/09_Daily_Logs/`.
- Append-only verdict log -> `experiments_log.md`.
- Structured verdict log -> `results/experiments.csv`
  (no bulk loads; read targeted rows only).

## Quick paths inside the wiki

- Topic indexes -> `obsidian/wiki/index/<topic>.md`.
- Per-source summaries -> `obsidian/wiki/summaries/`.
- Per-hypothesis decisions -> `obsidian/wiki/decisions/Hxxxx.md`.
- QC / Lean errors -> `obsidian/wiki/qc_lean/errors/`.
- QC / Lean patterns -> `obsidian/wiki/qc_lean/patterns/`.
- Lint snapshot history -> `obsidian/wiki/lint_history/`.

## Do-not-open by default

- `results/raw/`, `results/trades/`, `results/orders/`,
  `results/logs/`, `results/reports/`.
- Any file > 5 MB. Hard rule, always.
- `obsidian/04_Backtests/**/statistics.json` and `*_logs.txt`.
- `obsidian/raw/` (read the matching summary instead).
- Strategy `main.py` for hypotheses other than the one being worked on.

---

Below: original `00_Index.md` content, preserved verbatim.

---

## Folders

- `01_Rules/` — hard rules, falsification framework, fee/slippage model,
  no-leakage checklist, Monte Carlo protocol. Immutable without explicit
  user approval.
- `02_Hypotheses/` — active hypotheses. One file per hypothesis. Created
  by researcher mode. Moved to `05_Rejected/` or `06_Passed/` after
  verdict.
- `03_Strategies/` — short cross-reference notes linking hypothesis
  notes to the code folder under `strategies/`.
- `04_Backtests/` — one note per backtest run. Filled by the user with
  QC results and by auditor mode after Devin verdict.
- `05_Rejected/` — permanent graveyard. Never edited to look better.
  Codex must read this before proposing any new hypothesis.
- `06_Passed/` — hypotheses that cleared the full framework including
  Monte Carlo. Rare by design.
- `07_Lessons/` — generalizable lessons learned from rejected or
  inconclusive experiments. Not per-hypothesis detail.
- `08_Data_Notes/` — candidate edge notes, data availability notes (what
  is reliably available in QC Lean v17685 for Binance USD-M Futures,
  what is not, what is forbidden because it cannot be fabricated).
- `09_Daily_Logs/` — short daily research log. One file per calendar
  day.
- `10_Codex_Instructions/` — canned prompts for Codex modes and a
  per-task template for when you want to send a specific instruction to
  Codex that is larger than one sentence.

## ID scheme

- Hypothesis: `Hxxxx` (zero-padded, 4 digits). Next free IDs: H0002,
  H0005, H0007, H0008, ...
- Strategy cross-ref: `Sxxxx` — reuses the hypothesis number.
- Backtest report: `BTxxxx`.
- Candidate edge: `CExxxx`.
- Lesson: `Lxxxx`.

## Current state (seed)

- Rejected: H0001, H0003, H0004, H0006. See `05_Rejected/`.
- Lesson L0001: spot <=5m BTC/ETH/SOL mean-reversion and microtrend
  patterns did not produce an edge after realistic costs.

## Read order for Codex (deep dive)

1. `../.codex/AGENTS.md`
2. Everything in `01_Rules/`
3. Everything in `05_Rejected/`
4. `07_Lessons/`
5. `08_Data_Notes/`
