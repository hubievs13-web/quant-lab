# Step 8 verification + migration completion

Final note for the LLM Wiki migration described in
`PLAN_LLM_WIKI_MIGRATION.md`. This file confirms Steps 1-7 are
done and shows the expected token-cost reduction of the new
wiki-first read order.

## Migration completion

| Step | Status | PR |
|---|---|---|
| 1. Plan | done | #1 |
| 2. Skeleton files / folders / templates | done | #2 |
| 3. (combined with 2) | done | #2 |
| 4. LOW TOKEN MODE + wiki-first read order in protected files | done | #5 |
| 5. Case-aware rename `00_Index.md` -> `00_INDEX.md` + nav map | done | #3 |
| 6. Populate `00_HOT.md` v1 from canonical files | done | #4 |
| 7. Generate `00_LINT_REPORT.md` v1 | done | #6 |
| 8. This verification report | done | (this PR) |
| Cleanup A. H0002/H0005/H0007 frontmatter | done | #7 |
| Cleanup B. H0008 frontmatter awaiting_audit | done | #8 |
| Cleanup E. H0007 backtest gap reclassified | done | #9 |
| Cleanup C. Deduplicate QC-export-named files | DEFERRED | - |
| Cleanup D. Rename Smooth Blue Jellyfish folder | DEFERRED | - |
| Cleanup F. Per-hypothesis decision pages | absorbed into `decisions_index.md` | (this PR) |

## Expected token-cost reduction

File sizes (bytes / lines, measured with `wc`):

| File | Bytes | Lines |
|---|---|---|
| `MASTER_CONTEXT.md` | 18,449 | 319 |
| `.codex/AGENTS.md` | 16,678 | 407 |
| `README.md` | 6,570 | 166 |
| `obsidian/00_INDEX.md` | 4,920 | 119 |
| `obsidian/00_START_HERE.md` | 3,098 | 84 |
| `obsidian/00_HOT.md` | 1,290 | 39 |
| `PROJECT_INSTRUCTIONS.md` | 1,535 | 45 |

### Read scenarios

Scenario A (typical "what is the project state" query):

- Baseline (read `MASTER_CONTEXT.md`): ~18 KB.
- Wiki-first (read `00_START_HERE.md` + `00_HOT.md`): ~4.4 KB.
- Reduction: about 76 percent.

Scenario B (navigation-needed query, e.g. "where do rejected
hypotheses live?"):

- Baseline (read `MASTER_CONTEXT.md` + `.codex/AGENTS.md`): ~35 KB.
- Wiki-first (read `00_START_HERE.md` + `00_HOT.md` + `00_INDEX.md`):
  ~9.3 KB.
- Reduction: about 73 percent.

Scenario C (specific backtest metric query, e.g. "what was H0005
final Sharpe?"):

- Baseline (read `MASTER_CONTEXT.md` + open
  `Smooth Blue Jellyfish_H0005_2026-04-29/statistics.json`):
  ~18 KB + 2.9 MB. The 2.9 MB read alone violates the 5 MB rule
  by accident-prone reading patterns and dominates token cost.
- Wiki-first (read `00_HOT.md` + `obsidian/wiki/summaries/H0005_*.md`):
  ~1.3 KB + ~2.2 KB = ~3.5 KB.
- Reduction: more than 99 percent.

## Caveats

- These are file-byte numbers, not exact token counts. Real token
  cost depends on the LLM tokenizer and on how much of each file
  the agent actually keeps in context. The ratio is the relevant
  signal.
- The reduction holds only if agents follow the wiki-first read
  order in `.codex/AGENTS.md` Section 14 and stop at the smallest
  set of files that answers the query.
- Agents that ignore Section 14 and read `MASTER_CONTEXT.md` for
  every query erase the reduction.

## What this verification does NOT do

- Does not run a live LLM round-trip; the numbers above are
  bounds, not measured tokens.
- Does not modify any verdict, log, result, or strategy code.
- Does not promote H0008 past `awaiting_audit`.
- Does not generate or restore the missing H0007 backtest folder.

## Cross-links

- Plan: `PLAN_LLM_WIKI_MIGRATION.md`.
- Operating protocol: `obsidian/WIKI_OPERATING_PROTOCOL.md`.
- Hot state: `obsidian/00_HOT.md`.
- Lint snapshot: `obsidian/00_LINT_REPORT.md`.
- Decisions: `obsidian/wiki/decisions/decisions_index.md`.
- Backtest summaries: `obsidian/wiki/summaries/`.
