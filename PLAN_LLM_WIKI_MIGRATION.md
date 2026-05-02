# PLAN_LLM_WIKI_MIGRATION

Status: DRAFT — awaiting user approval. No implementation yet.

Scope: design (only) a Karpathy-style LLM Wiki layer inside `obsidian/`
that helps Codex / Devin operate in a low-token, targeted mode without
replacing the existing quant research pipeline.

Pipeline preserved as-is:
idea -> hypothesis -> evidence -> pre-backtest gates -> code -> smoke
test -> full backtest -> Monte Carlo -> verdict.

Hard constraints honored throughout this plan:

- No rewrite of trading strategy code.
- No change to any final verdict.
- No deletion of existing notes, results, logs, or strategy packages.
- No RAG, vector DB, embeddings, MCP server, web app, or new
  dependencies.
- No full-repo scans by default.
- No reading of files larger than 5 MB without explicit approval.
- For large files: index / summary notes only.
- No touching of large raw data or backtest artifacts unless required.
- `MASTER_CONTEXT.md`, `PROJECT_INSTRUCTIONS.md`, and
  `.codex/AGENTS.md` only get edits for token efficiency, navigation,
  and agent operating rules.
- All logs append-only. No silent overwrites of history.

---

## 0. Current state snapshot (read targeted, not exhaustive)

Files / folders inspected for this plan only (no edits made):

- `README.md`, `PROJECT_INSTRUCTIONS.md`, `MASTER_CONTEXT.md`,
  `MASTER_CONTEXT_UPDATE_PROTOCOL.md`, `experiments_log.md`.
- `.codex/AGENTS.md`, `.codex/README.md`,
  `.codex/roles/{researcher,engineer,auditor}.md`.
- `obsidian/00_Index.md` and folder listing of `obsidian/01_Rules/`,
  `02_Hypotheses/`, `03_Strategies/`, `04_Backtests/`, `05_Rejected/`,
  `06_Passed/`, `07_Lessons/`, `08_Data_Notes/`, `09_Daily_Logs/`,
  `10_Codex_Instructions/`.
- `results/README.md`, `results/experiments.csv` (header + 2 rows).
- `research/README.md`, `strategies/README.md`.

Key facts that drive this plan:

- Active hypotheses: H0008.
- Rejected: H0001, H0002, H0003, H0004, H0005, H0006, H0007.
- Lessons: L0001, L0002, L0005, L0006.
- One large file already in vault:
  `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/statistics.json`
  ~2.9 MB. Under 5 MB but heavy; agents should not read it directly.
- User local paths suggest Windows. Filename case can be ambiguous on
  Windows (case-insensitive filesystem). This affects the rename of the
  existing `obsidian/00_Index.md` to the requested `obsidian/00_INDEX.md`.
  Treated as a migration risk below.

---

## 1. Files to create

All paths are relative to repo root.

New, non-destructive (additive only):

1. `obsidian/00_START_HERE.md`
   - First file every agent reads.
   - Hard cap: ~80 lines.
   - Contents: read order, low-token mode pointer, "do not scan repo"
     rule, link to `00_HOT.md`, `00_INDEX.md`, `WIKI_OPERATING_PROTOCOL.md`.

2. `obsidian/00_HOT.md`
   - Shortest current project state.
   - Hard cap: ~40 lines.
   - Contents: current phase, last verdict, active hypothesis ID,
     last 3 rejected IDs, top forbidden follow-ups, top open question.
   - Updated by Codex auditor mode after every verdict.

3. `obsidian/00_INGEST_LOG.md`
   - Append-only log of every source ingested into `obsidian/wiki/`.
   - Format per line:
     `YYYY-MM-DD | source_path | summary_path | status | reason`.
   - Status values: ingested | summarized | superseded | rejected.
   - Never edit prior lines.

4. `obsidian/00_LINT_REPORT.md`
   - Wiki health report.
   - Generated / updated only when explicitly requested.
   - Sections: duplicates, stale notes, broken links, unclear status,
     missing evidence, oversize files (>5 MB or >2000 lines).
   - Always overwritten as a snapshot, but every snapshot timestamped
     and the previous snapshot moved to `obsidian/wiki/lint_history/`
     so history is never lost (append-only at the directory level).

5. `obsidian/WIKI_OPERATING_PROTOCOL.md`
   - Rules for ingest, lint, token usage, verdict handling, and
     QuantConnect / Lean error handling.
   - This is the wiki's constitution. Codex must read it before any
     wiki write.

6. `obsidian/wiki/` (new folder)
   - Compact processed knowledge notes. Each note is a summary of one
     or more raw sources.
   - Subfolders proposed:
     - `wiki/index/`           one-page topic indexes (e.g.,
       `funding.md`, `basis.md`, `microstructure.md`,
       `qc_lean_errors.md`).
     - `wiki/summaries/`       per-source compact summaries (referenced
       from `00_INGEST_LOG.md`).
     - `wiki/decisions/`       short notes that capture
       hypothesis-level decisions (active / rejected / passed) in a
       form Codex can scan in one read.
     - `wiki/qc_lean/`         QuantConnect / Lean v17685 error
       patterns and known fixes (see Section 9).
     - `wiki/lint_history/`    timestamped snapshots of
       `00_LINT_REPORT.md`.

7. `obsidian/raw/` (new folder)
   - Unprocessed sources Codex chose to keep verbatim.
   - Files here are NEVER read by default. Always summarized into
     `obsidian/wiki/summaries/` first; agents read the summary.
   - Files >5 MB are forbidden here unless the user approves.

8. `obsidian/templates/` (new folder)
   - Reusable templates for the new wiki layer only. Existing
     templates under `02_Hypotheses/_TEMPLATE_*.md`,
     `03_Strategies/_TEMPLATE_*.md`, etc., are NOT moved or renamed.
   - Files proposed:
     - `templates/_TEMPLATE_wiki_summary.md`
     - `templates/_TEMPLATE_wiki_index.md`
     - `templates/_TEMPLATE_wiki_decision.md`
     - `templates/_TEMPLATE_qc_lean_error.md`

Total: 6 new top-level Markdown files under `obsidian/`, 5 new folders
under `obsidian/`, 4 new templates. Zero existing files deleted or
renamed without explicit approval (see Section 10 risk on `00_INDEX.md`).

---

## 2. Files to modify

All edits in this section are PROPOSED only. Nothing is implemented in
this plan PR. Each edit is small, additive, and motivated strictly by
token efficiency, navigation, or agent operating rules.

### 2.1 `.codex/AGENTS.md`

Proposed additions (no removals, no rewording of existing rules):

- New section: "Wiki-first reading order".
  - Codex must read `obsidian/00_START_HERE.md` first.
  - Then `obsidian/00_HOT.md`.
  - Then `obsidian/00_INDEX.md` only when navigation is needed.
  - Then targeted linked files only.
- New section: "LOW TOKEN MODE" (full text in Section 12 below).
- New rule: "Never scan the whole repository by default."
- New rule: "Never read files larger than 5 MB without explicit user
  approval."
- New rule: "Prefer `obsidian/wiki/` summaries over raw files."
- New rule: "Append logs only; never overwrite history."
- New cross-reference: link to `obsidian/WIKI_OPERATING_PROTOCOL.md`.

These are agent-operating rules and navigation only. No change to:
mission, falsification framework, hard rules 1-12, fee model, rejected
mechanism table, or verdict authority.

### 2.2 `PROJECT_INSTRUCTIONS.md`

Proposed additions:

- "Wiki-first session bootstrap" pointing at
  `obsidian/00_START_HERE.md` and `obsidian/00_HOT.md`.
- Reaffirm: read `MASTER_CONTEXT.md` only when full handoff context is
  needed, not by default.
- Add the LOW TOKEN MODE section.

No change to MASTER_CONTEXT update policy.

### 2.3 `MASTER_CONTEXT.md`

Proposed additions:

- Top-of-file "How to use this file" block: read only when full handoff
  is required; otherwise prefer `obsidian/00_HOT.md`.
- A "Wiki pointers" section listing:
  - `obsidian/00_START_HERE.md`
  - `obsidian/00_HOT.md`
  - `obsidian/00_INDEX.md`
  - `obsidian/WIKI_OPERATING_PROTOCOL.md`

No change to: current status, rejected list, latest verdict, lessons,
forbidden follow-ups, allowed next directions. The existing update
protocol in `MASTER_CONTEXT_UPDATE_PROTOCOL.md` still governs all
hypothesis-cycle updates.

### 2.4 `.codex/roles/researcher.md`, `engineer.md`, `auditor.md`

Proposed additions to each role file (one short block per file):

- "Default reading order" pointing at `00_START_HERE.md` -> `00_HOT.md`
  -> targeted files. Existing required-reading lists are kept and only
  appended to if needed; nothing removed.
- "LOW TOKEN MODE" block (same canonical text in all three files).
- Auditor specifically: add a duty to update `obsidian/00_HOT.md` on
  verdict events. (Existing `MASTER_CONTEXT.md` update duty is
  unchanged.)

### 2.5 `obsidian/00_Index.md`

This is the existing camelCase index file. The required structure
specifies `00_INDEX.md` (uppercase). On Windows the filesystem is
case-insensitive, so `00_Index.md` and `00_INDEX.md` collide.

Proposed handling (requires user approval, see Section 11):

- Option A (preferred): rename `00_Index.md` to `00_INDEX.md` via a
  Git case-aware rename. Preserve all current content; add the new
  navigation map sections at the top.
- Option B: keep `00_Index.md` as-is and create `00_INDEX.md`
  separately. NOT recommended: collides on Windows.

Either way, no content is lost.

### 2.6 `obsidian/10_Codex_Instructions/*.md`

Proposed: append a short "LOW TOKEN MODE" reminder to each canned
prompt (`researcher_prompt.md`, `engineer_prompt.md`,
`auditor_prompt.md`, `master_context_update_prompt.md`). Existing
content is kept verbatim.

### 2.7 `README.md`

Proposed: a single new short subsection "Wiki-first navigation for
agents" that points at `obsidian/00_START_HERE.md` and
`obsidian/WIKI_OPERATING_PROTOCOL.md`. No change to project structure
description, lifecycle of a hypothesis, or evidence policy.

---

## 3. Files / folders that must NOT be read by default

Codex / Devin must NOT open any of these unless the current task
explicitly requires it AND (where noted) the user has approved:

- The whole repository tree. No directory walks at session start.
- `results/raw/` (when present) and any QC export bundles.
- `results/trades/`, `results/orders/`, `results/logs/`,
  `results/reports/`.
- `results/experiments.csv` beyond the latest relevant row (use the
  Obsidian backtest report instead).
- `obsidian/04_Backtests/**/statistics.json` and any `*_logs.txt`
  inside backtest folders. Specifically known oversize artifact:
  `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/statistics.json`
  (~2.9 MB).
- `obsidian/04_Backtests/**/*.json` and `*.txt` larger than 200 KB.
  For these, agents must read only the corresponding `report.md`
  summary.
- Any file > 5 MB. Hard rule, always.
- `obsidian/raw/` once it exists. Read the matching summary in
  `obsidian/wiki/summaries/` instead.
- `scripts/` source code unless the task is editing those scripts.
  Operational behavior is documented in `.codex/README.md`.
- Strategy `main.py` files for unrelated hypotheses. Only the strategy
  for the hypothesis under work is loaded.

---

## 4. How existing artifacts are preserved

Nothing existing is deleted. Specifically:

1. `MASTER_CONTEXT.md`
   - Stays as the canonical handoff file.
   - Continues to be updated per `MASTER_CONTEXT_UPDATE_PROTOCOL.md`.
   - Only top-of-file pointer block is added (Section 2.3).
   - Verdict text and rejected lists are not touched by this
     migration.

2. `PROJECT_INSTRUCTIONS.md`
   - Stays. Only additive edits per Section 2.2.

3. `.codex/AGENTS.md`
   - Stays. Hard rules 1-12, falsification framework, rejected
     mechanism table are NOT changed. Only additive sections per
     Section 2.1.

4. `experiments_log.md`
   - Append-only, untouched. The new wiki never edits prior lines.
   - Auditor mode keeps appending one line per verdict as today.

5. `results/experiments.csv`
   - Untouched by the wiki layer. Still maintained by
     `scripts/process_qc_backtest.py`.
   - The wiki references rows by `backtest_id` instead of duplicating
     numbers.

6. Existing Obsidian content
   - `obsidian/01_Rules/` through `obsidian/10_Codex_Instructions/`:
     untouched, except for the `00_Index.md` -> `00_INDEX.md` rename
     question (Section 2.5, Section 10) and small additive edits to
     `10_Codex_Instructions/*.md` (Section 2.6).
   - All hypothesis notes (`02_Hypotheses/`), rejected notes
     (`05_Rejected/`), passed notes (`06_Passed/`), backtest notes
     (`04_Backtests/`), data notes (`08_Data_Notes/`), lessons
     (`07_Lessons/`), and daily logs (`09_Daily_Logs/`) remain the
     authoritative source of truth.

7. Strategy code under `strategies/`
   - Not modified. The wiki only references strategy folders.

The wiki is a NAVIGATION + SUMMARY layer. It is not a replacement for
any existing artifact.

---

## 5. Proposed `obsidian/` wiki structure

```
obsidian/
  00_START_HERE.md              new  agent first read
  00_HOT.md                     new  shortest current state
  00_INDEX.md                   new  navigation map (replaces 00_Index.md
                                     via case-aware rename, content
                                     preserved + extended)
  00_INGEST_LOG.md              new  append-only ingest log
  00_LINT_REPORT.md             new  wiki health snapshot
  WIKI_OPERATING_PROTOCOL.md    new  wiki rules / token budgets
  raw/                          new  unprocessed sources, never read by default
  wiki/                         new  compact processed notes
    index/                      new  topic indexes (one page each)
    summaries/                  new  per-source compact summaries
    decisions/                  new  hypothesis-level decisions snapshot
    qc_lean/                    new  QC / Lean error patterns
    lint_history/               new  timestamped lint snapshots
  templates/                    new  wiki-only templates

  01_Rules/                     unchanged
  02_Hypotheses/                unchanged
  03_Strategies/                unchanged
  04_Backtests/                 unchanged
  05_Rejected/                  unchanged
  06_Passed/                    unchanged
  07_Lessons/                   unchanged
  08_Data_Notes/                unchanged
  09_Daily_Logs/                unchanged
  10_Codex_Instructions/        small additive edits only (Section 2.6)
```

Cross-linking pattern (one direction, to avoid duplicate truth):

- `obsidian/wiki/decisions/H0008.md` -> links to
  `obsidian/02_Hypotheses/H0008_funding_premium_crowding_unwind.md`
  and `obsidian/03_Strategies/S0008_funding_premium_crowding_unwind.md`.
- `obsidian/wiki/decisions/H0007.md` -> links to
  `obsidian/05_Rejected/H0007_funding_settlement_unwind.md` and
  `obsidian/07_Lessons/L0006_funding_settlement_unwind_failed.md`.
- The wiki note never restates the verdict; it only points to the
  authoritative file.

---

## 6. How this reduces token usage

Mechanisms (no new dependencies, no embeddings):

1. Bounded entry point. Agents read `00_START_HERE.md` first, capped
   at ~80 lines, instead of arbitrary discovery.

2. Hot-state cache. `00_HOT.md` (~40 lines) replaces re-reading
   `MASTER_CONTEXT.md` (currently ~295 lines) for routine queries.

3. Targeted navigation. `00_INDEX.md` provides a one-page map; agents
   stop using grep / find to discover folders.

4. Summaries before raw. For any source > 200 KB, the wiki holds a
   compact summary in `obsidian/wiki/summaries/` and the agent reads
   the summary. Raw only when explicitly required by the task.

5. 5 MB hard ceiling. Forbids accidental loads of large JSON / log
   exports.

6. Decision snapshots. Per-hypothesis decision pages aggregate verdict
   + rejected reasons + lessons in one short page, removing the need
   to open 4 separate notes.

7. QC / Lean error library. `obsidian/wiki/qc_lean/` holds short
   pattern -> fix entries. Stops Codex from re-deriving the same
   diagnostic.

8. Concise output policy. LOW TOKEN MODE forces short answers, one
   next action, no theory unless requested.

9. Stable read order. Identical bootstrap on every session means no
   exploration loops.

10. No background scans. Codex never reads `results/`, `strategies/`
    sources, or large backtest artifacts unless the active task
    requires that exact file.

---

## 7. How this prevents repeated mistakes

1. `obsidian/wiki/decisions/Hxxxx.md` exposes the rejected /
   passed / active status of every hypothesis on a single line near
   the top. Mistakes happen when status is buried.

2. `obsidian/wiki/index/` topic indexes link rejected mechanisms
   alongside the active ones. A researcher looking up "funding" sees
   H0007 rejected before drafting a new funding hypothesis.

3. `obsidian/wiki/qc_lean/` records "errors we have seen" in compact
   form. Codex queries this before guessing.

4. `00_LINT_REPORT.md` flags duplicates, broken links, and unclear
   statuses. If a hypothesis is partially in two folders or has an
   inconsistent verdict marker, lint surfaces it before the agent
   acts.

5. `00_INGEST_LOG.md` records what was ingested and into which
   summary. Prevents Codex from re-summarizing the same source twice
   or losing track of which source produced a given summary.

6. The required `WIKI_OPERATING_PROTOCOL.md` enforces:
   - Never revive a rejected hypothesis without external evidence.
   - Never tune.
   - Never overwrite verdicts.
   - Never auto-promote a hypothesis from rejected to active.

---

## 8. How active / rejected / passed status is protected

Status truth lives where it lives today:

- Active: `obsidian/02_Hypotheses/Hxxxx_*.md`.
- Rejected: `obsidian/05_Rejected/Hxxxx_*.md` (or
  `pre_backtest_rejected/`).
- Passed: `obsidian/06_Passed/Hxxxx_*.md`.
- Verdict log: `experiments_log.md`, `results/experiments.csv`.

The wiki layer never sets status. It only reads it. Specifically:

- `obsidian/wiki/decisions/Hxxxx.md` derives status by reading the
  authoritative file path. If the same Hxxxx appears in two of
  {02_Hypotheses, 05_Rejected, 06_Passed}, lint flags it as a
  duplicate-status defect; no agent silently picks one.

- `WIKI_OPERATING_PROTOCOL.md` codifies:
  - Status changes happen only via the existing auditor flow defined
    in `.codex/roles/auditor.md`.
  - Hypothesis files are MOVED, never deleted (existing rule from
    AGENTS.md section 8).
  - Wiki notes are regenerated from the canonical files, not edited
    in place to reflect a status change.

- The lint check explicitly looks for "wiki disagrees with canonical":
  if `wiki/decisions/H0007.md` says active but the file lives in
  `05_Rejected/`, lint marks it as a defect to fix in the wiki, not in
  the canonical store.

---

## 9. How QuantConnect / Lean errors are handled

Today: Codex re-derives Lean error meaning from logs each time.
Proposal: a small, append-only error library inside the wiki.

Layout:

```
obsidian/wiki/qc_lean/
  README.md
  errors/
    QCERR-0001_<short_slug>.md
    QCERR-0002_<short_slug>.md
    ...
  patterns/
    next_bar_execution.md
    custom_fee_model.md
    futures_universe.md
    ...
```

Each `QCERR-xxxx_*.md` note (filled from
`templates/_TEMPLATE_qc_lean_error.md`) contains:

- One-line symptom (exact log substring match if possible).
- Lean version (currently v17685).
- Where it came from (backtest ID, hypothesis, log file path).
- Root cause (short).
- Confirmed fix or workaround.
- Forbidden follow-ups (e.g., "do not retry by tuning param X").
- Status: open / resolved / known-limitation.

Update flow:

1. When Codex sees a Lean error during engineer or auditor work, it
   first searches `obsidian/wiki/qc_lean/errors/` by symptom.
2. If found: apply the recorded fix.
3. If not found: open a new `QCERR-xxxx_*.md`, status `open`.
4. When user confirms a fix worked: status flips to `resolved`. The
   prior content is preserved; resolution is appended in a new
   section.
5. `QCERR` notes never overwrite history. They only append.

Boundary:

- This library does not change the verdict of any backtest.
- It does not authorize tuning a rejected hypothesis. AGENTS.md
  section 5 rule 1 (no tuning) still wins.

---

## 10. Migration risks

1. Filename case collision (Windows-only):
   `obsidian/00_Index.md` already exists. The required name is
   `obsidian/00_INDEX.md`. On case-insensitive filesystems these
   collide. Mitigation: explicit Git case-aware rename
   (`git mv 00_Index.md 00_INDEX.md` two-step via temporary name).
   Requires user approval.

2. Two indexes drift apart. Risk: someone edits `00_Index.md` after
   the rename. Mitigation: only one file exists post-rename.

3. Hot-state staleness. Risk: `00_HOT.md` lags behind real status.
   Mitigation: auditor role gets an explicit "update 00_HOT.md" step
   on every verdict (Section 2.4).

4. Wiki decision file contradicts canonical file. Mitigation: lint
   check (Section 7).

5. Token regression on first session. The first session that ingests
   existing content into `obsidian/wiki/summaries/` will be expensive.
   Mitigation: ingest only on demand, one source per task; never bulk
   import.

6. Accidental large-file read. Mitigation: 5 MB hard ceiling encoded
   in `WIKI_OPERATING_PROTOCOL.md` and AGENTS.md addition (Section
   2.1).

7. Existing 2.9 MB backtest artifact
   (`Smooth Blue Jellyfish_H0005_2026-04-29/statistics.json`). Under
   the 5 MB ceiling but heavy. Mitigation: explicit do-not-read entry
   in `obsidian/wiki/summaries/` and in Section 3 above.

8. Confusion between `obsidian/raw/` (new) and `results/raw/`
   (existing). Mitigation: protocol states clearly that
   `obsidian/raw/` is for unprocessed knowledge sources only;
   QuantConnect exports keep going to `results/raw/`.

9. Duplicate templates risk. Mitigation: `obsidian/templates/` only
   contains wiki-layer templates; existing per-folder
   `_TEMPLATE_*.md` files are not moved or duplicated.

10. Hidden optimization risk. Wiki summaries must not editorialize.
    Mitigation: protocol says summaries are quote-or-cite, never
    rewrite verdicts or thresholds.

---

## 11. Actions that require user approval

Listed in priority order. Implementation is gated on each item.

A. Approve the plan as a whole (this file).

B. Approve the rename `obsidian/00_Index.md` -> `obsidian/00_INDEX.md`.

C. Approve creation of new top-level wiki files:
   `00_START_HERE.md`, `00_HOT.md`, `00_INGEST_LOG.md`,
   `00_LINT_REPORT.md`, `WIKI_OPERATING_PROTOCOL.md`.

D. Approve creation of new folders: `obsidian/raw/`, `obsidian/wiki/`
   (with subfolders as listed in Section 5), `obsidian/templates/`.

E. Approve additive edits to:
   - `.codex/AGENTS.md` (Section 2.1)
   - `PROJECT_INSTRUCTIONS.md` (Section 2.2)
   - `MASTER_CONTEXT.md` (Section 2.3)
   - `.codex/roles/{researcher,engineer,auditor}.md` (Section 2.4)
   - `obsidian/10_Codex_Instructions/*.md` (Section 2.6)
   - `README.md` (Section 2.7)

F. Approve the LOW TOKEN MODE text in Section 12 below as the
   canonical block to insert.

G. Approve the do-not-read default list (Section 3).

H. Optional: approve a one-time lint pass of existing wiki content
   that produces `00_LINT_REPORT.md` v1. No file is changed by lint;
   it only reports.

Anything not on this list is not part of this migration.

---

## 12. LOW TOKEN MODE (proposed canonical block)

This is the exact block proposed for insertion into `.codex/AGENTS.md`,
`PROJECT_INSTRUCTIONS.md`, the three `.codex/roles/*.md` files, and (as
a one-line pointer plus link) into `MASTER_CONTEXT.md` and `README.md`.

```
## LOW TOKEN MODE

Default response style: short, direct, no motivational text.

Default workflow: inspect only the minimum required files.

Default file reading order:
1. obsidian/00_START_HERE.md
2. obsidian/00_HOT.md
3. obsidian/00_INDEX.md if navigation is needed
4. targeted linked files only

Forbidden by default:
- full repo scans
- reading large files (> 5 MB always; > 200 KB without need)
- reading raw backtest artifacts
- rewriting entire files when a small patch is enough
- repeating background context
- coding before research gates pass

Output format:
- what I checked
- what I changed or propose to change
- exact next step
- no long theory unless requested

Concrete behavior rules:
1. Codex must not read the full repository by default.
2. Codex must start with obsidian/00_START_HERE.md and
   obsidian/00_HOT.md.
3. Codex must read MASTER_CONTEXT.md only when the task requires full
   project handoff context.
4. Codex must read PROJECT_INSTRUCTIONS.md only when project-level
   operating rules are needed.
5. Codex must use obsidian/00_INDEX.md for navigation instead of
   searching randomly.
6. Codex must prefer compact wiki summaries over raw files.
7. Codex must never read files larger than 5 MB without explicit user
   approval.
8. Codex must not open results/raw/, data/, or large backtest
   artifacts unless explicitly required.
9. Codex must answer in concise mode by default.
10. Codex must avoid long explanations unless the user asks.
11. Codex must provide one concrete next action instead of broad
    multi-option advice.
12. Codex must not repeat known project context in every response.
13. Codex must not restate the full research pipeline unless relevant.
14. Codex must ask clarifying questions only when the task is blocked.
15. Codex must make the smallest safe file change needed for the task.
16. Codex must prefer patches/diffs over rewriting whole files.
17. Codex must append logs instead of rewriting history.
18. Codex must not create new files unless needed.
19. Codex must not create new abstractions, folders, frameworks, or
    dependencies without approval.
20. Codex must stop after completing the requested step and wait for
    the next instruction.
```

Files that will receive the full block (verbatim) once approved:

- `.codex/AGENTS.md`
- `PROJECT_INSTRUCTIONS.md`
- `.codex/roles/researcher.md`
- `.codex/roles/engineer.md`
- `.codex/roles/auditor.md`

Files that will receive a short pointer to the block (one paragraph
+ link) so the canonical text lives in one place:

- `MASTER_CONTEXT.md`
- `README.md`
- `obsidian/00_START_HERE.md`
- `obsidian/WIKI_OPERATING_PROTOCOL.md`
- `obsidian/10_Codex_Instructions/researcher_prompt.md`
- `obsidian/10_Codex_Instructions/engineer_prompt.md`
- `obsidian/10_Codex_Instructions/auditor_prompt.md`
- `obsidian/10_Codex_Instructions/master_context_update_prompt.md`

This avoids token bloat from duplicated rule text while keeping the
rules discoverable from every entry point.

---

## Clear next steps after approval

Once the user explicitly approves this plan (and the items listed in
Section 11), implementation proceeds in this fixed order. Each step is
a separate small change set; agent stops after each step and waits.

Step 1. Create the six new top-level wiki files in `obsidian/` with
        skeletons (templates only, no content from raw scans).

Step 2. Create the new folders: `obsidian/raw/`, `obsidian/wiki/` and
        subfolders, `obsidian/templates/`. Add `.gitkeep` where needed.

Step 3. Add the four new wiki templates under `obsidian/templates/`.

Step 4. Apply the additive edits to `.codex/AGENTS.md`,
        `PROJECT_INSTRUCTIONS.md`, `MASTER_CONTEXT.md`, the three role
        files, the canned-prompt files, and `README.md`.

Step 5. Case-aware rename `obsidian/00_Index.md` ->
        `obsidian/00_INDEX.md`. Preserve content; extend with the new
        navigation map.

Step 6. Generate `obsidian/00_HOT.md` v1 from current canonical files
        only (no full-repo scan):
        `MASTER_CONTEXT.md` (latest section), `experiments_log.md`
        (last line), `obsidian/02_Hypotheses/` (active),
        `obsidian/05_Rejected/` (count + last 3 IDs).

Step 7. Optional: produce `obsidian/00_LINT_REPORT.md` v1 (read-only
        report, no file changes).

Step 8. Begin per-task ingest into `obsidian/wiki/summaries/` only
        when a real task requires it. No bulk import. Each ingest
        appends one line to `obsidian/00_INGEST_LOG.md`.

Nothing else is in scope for this migration.

---

## End of plan

No code, no notes, no instruction files have been changed by this PR.
Only this file (`PLAN_LLM_WIKI_MIGRATION.md`) has been added at the
repository root. Implementation is gated on user approval per Section
11.
