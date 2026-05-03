# 00_LINT_REPORT

Wiki health snapshot. v1 (first run).

This file is generated on demand. The lint pass is read-only and
NEVER edits other files. It only reports findings; cleanup is a
separate, gated action.

## Last run

- Date: 2026-05-02
- Scope: lightweight repo metadata only — file paths, sizes, YAML
  frontmatter of small notes. No file > 200 KB read. No raw
  results / data folders read.
- Sources inspected: `obsidian/00_*.md`, `obsidian/02_Hypotheses/`,
  `obsidian/03_Strategies/`, `obsidian/04_Backtests/` (folder
  listing + sizes only; no JSON read), `obsidian/05_Rejected/`
  (frontmatter only), `obsidian/06_Passed/`, `obsidian/07_Lessons/`
  (listing only), `obsidian/08_Data_Notes/` (listing only),
  `obsidian/10_Codex_Instructions/`, `obsidian/templates/`,
  `experiments_log.md` (last 3 lines), `strategies/` (folder
  listing only).

## 1. Duplicate / overlapping wiki files

- `obsidian/04_Backtests/BT0001_H0002_2026-04-29/Swimming Black Panda.json`
  is byte-identical to `statistics.json` in the same folder
  (both 597,795 B). Likely intentional QC-export-name
  preservation, but redundant on disk.
- `obsidian/04_Backtests/BT0001_H0002_2026-04-29/Swimming Black Panda_logs.txt`
  is byte-identical to `logs.txt` in the same folder
  (both 103,016 B). Same redundancy as above.
- Backtest folder naming is inconsistent: one folder uses the
  canonical `BTxxxx_Hxxxx_YYYY-MM-DD` pattern
  (`BT0001_H0002_2026-04-29/`); the other uses the QC export name
  (`Smooth Blue Jellyfish_H0005_2026-04-29/`). Convention drift.

## 2. Broken internal links

- None detected in the new wiki layer files
  (`00_START_HERE.md`, `00_HOT.md`, `00_INDEX.md`,
  `00_INGEST_LOG.md`, `WIKI_OPERATING_PROTOCOL.md`,
  `templates/_TEMPLATE_*.md`).
- All hypothesis / strategy / candidate-edge cross-references
  referenced in `00_HOT.md` resolve
  (H0008, S0008, CE0021, `strategies/H0008_*`).

## 3. Stale references

- All five known stale `obsidian/00_Index.md` (lowercase)
  references were corrected in PR #5 follow-up (commit `e625072`).
- Remaining `00_Index.md` mentions are intentional historical
  context, not stale paths:
  - `obsidian/00_INDEX.md:6` — describes the case-aware rename in
    the renamed file's preamble.
  - `PLAN_LLM_WIKI_MIGRATION.md` — 13 mentions describing the
    rename plan, options, risks, and execution. Replacing them
    mechanically would make the plan incoherent.

## 4. Unclear hypothesis statuses (frontmatter drift)

Authoritative store: file location (`02_Hypotheses/` vs
`05_Rejected/` vs `06_Passed/`). Frontmatter `status:` field has
drifted from the canonical store in 4 cases.

- H0002 — file under `05_Rejected/`, frontmatter `status: draft`.
  Should read `rejected`. Verdict in `experiments_log.md`
  (2026-04-29): FAIL / REJECTED.
- H0005 — file under `05_Rejected/`, frontmatter `status: draft`.
  Should read `rejected`. Verdict in `experiments_log.md`
  (2026-04-29): FAIL / REJECTED.
- H0007 — file under `05_Rejected/`, frontmatter `status: draft`.
  Should read `rejected`. Verdict in `experiments_log.md`
  (2026-05-01): FAIL / REJECTED.
- H0008 — file under `02_Hypotheses/`, frontmatter `status: draft`.
  An engineered package exists at
  `strategies/H0008_funding_premium_crowding_unwind/` and
  `obsidian/03_Strategies/S0008_funding_premium_crowding_unwind.md`,
  so the hypothesis has progressed past pure draft. Status field
  needs verification by the project owner; suggested values per
  the existing taxonomy: `engineered` or `awaiting_audit`.

H0001, H0003, H0004, H0006 frontmatter is correct (`rejected`).

## 5. Missing evidence links

- `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/`
  is missing PRIMARY evidence files per `README.md` (l.127):
  `trades.csv` and `orders.csv`. Folder has only `logs.txt`,
  `report.md`, `statistics.json`.
- `obsidian/04_Backtests/BT0001_H0002_2026-04-29/` is missing
  PRIMARY evidence files: `trades.csv` and `orders.csv`.
- H0007 has a verdict line in `experiments_log.md` (2026-05-01,
  FAIL / REJECTED, "Determined Orange Mule" run) but **no
  backtest folder exists** under `obsidian/04_Backtests/`.
  Evidence trail for the H0007 verdict is not in the vault.

## 6. Oversize files (do-not-read-by-default)

Per LOW TOKEN MODE (`.codex/AGENTS.md` Section 14), agents must
not read these without explicit user approval.

- `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/statistics.json`
  — 2,989,640 B (~2.9 MB). Known oversize.
- `obsidian/04_Backtests/BT0001_H0002_2026-04-29/statistics.json`
  — 597,795 B (~584 KB).
- `obsidian/04_Backtests/BT0001_H0002_2026-04-29/Swimming Black Panda.json`
  — 597,795 B (~584 KB; duplicate of `statistics.json`).
- No file > 5 MB anywhere under `obsidian/`.

## 7. Files that should be summarized into `obsidian/wiki/`

- `wiki/summaries/BT0001_H0002_summary.md` — distill key metrics
  from `BT0001_H0002_2026-04-29/statistics.json` so agents do
  not re-read the ~584 KB JSON.
- `wiki/summaries/H0005_smooth_blue_jellyfish_summary.md` — same
  for the ~2.9 MB H0005 statistics file.
- `wiki/decisions/Hxxxx.md` for each rejected hypothesis (H0001,
  H0002, H0003, H0004, H0005, H0006, H0007) — one paragraph each
  with mechanism, verdict, and post-mortem highlight, so agents
  can answer "why was Hxxxx rejected?" without re-reading the
  full notes.
- `wiki/qc_lean/errors/` entries for any recurring QC/Lean errors
  in the two existing `logs.txt` files (~103 KB each) — only if
  worth indexing; defer until a recurring pattern shows up.

## 8. Cleanup actions

### Resolved

1. Bump frontmatter `status:` for H0002, H0005, H0007 from
   `draft` to `rejected` — DONE in PR #7.
2. Confirm and update H0008 frontmatter `status:` — DONE in
   PR #8 (`draft` -> `awaiting_audit`).
5. Investigate the missing H0007 backtest folder — DONE; per
   Cleanup E (PR #9) the folder was never generated, see
   "Explained gaps" sub-section above.
6. Generate wiki summary notes — DONE in the migration-completion
   batch PR: `obsidian/wiki/summaries/BT0001_H0002_2026-04-29.md`,
   `obsidian/wiki/summaries/H0005_smooth_blue_jellyfish_2026-04-29.md`,
   `obsidian/wiki/decisions/decisions_index.md`,
   `obsidian/wiki/index/step_8_verification.md`.

### Deferred known issues

3. Duplicate JSON / log file pairs in
   `obsidian/04_Backtests/BT0001_H0002_2026-04-29/`
   (`Swimming Black Panda.json` byte-identical to `statistics.json`;
   `Swimming Black Panda_logs.txt` byte-identical to `logs.txt`).
   Decision deferred — `README.md` l.140 prohibits deletion;
   moving QC-export-named copies to a sub-folder is the safer
   option but requires user approval. Tracked here, not auto-applied.
4. Folder `Smooth Blue Jellyfish_H0005_2026-04-29/` uses raw QC
   export name instead of canonical `BTxxxx_H0005_2026-04-29/`.
   Case-aware Git rename deferred. Tracked here, not auto-applied.
