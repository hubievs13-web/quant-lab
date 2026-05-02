# 00_LINT_REPORT

Wiki health snapshot. Skeleton (v0).

This file is generated on demand. The previous snapshot is moved to
`obsidian/wiki/lint_history/YYYY-MM-DDTHHMM_lint_report.md` so
history is preserved (append-only at the directory level).

The lint pass NEVER edits other files. It only reports.

## Last run

(none yet)

## Sections

When generated, this file contains the following sections:

1. Duplicates
   - Same hypothesis ID present in more than one of
     `02_Hypotheses/`, `05_Rejected/`, `06_Passed/`.
   - Same strategy ID referenced from multiple folders.
   - Same lesson recorded twice.

2. Stale notes
   - Files not touched for > N days that reference an active
     hypothesis whose status has since changed.
   - Backtest reports without a verdict line.

3. Broken links
   - Internal Markdown links that do not resolve.

4. Unclear status
   - Hypothesis files whose body says "rejected" but live outside
     `05_Rejected/`, or vice versa.
   - Wiki decision pages that disagree with the canonical store.

5. Missing evidence
   - Backtest reports without `trades.csv` / `orders.csv` /
     `logs.txt` / statistics file.
   - Hypotheses without a candidate edge note.

6. Oversize files
   - Files > 5 MB anywhere under `obsidian/`.
   - Files > 200 KB inside `obsidian/04_Backtests/` that are not
     `report.md`.

## Defects

(none yet)
