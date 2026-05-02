# Project Instructions

## MASTER_CONTEXT policy

MASTER_CONTEXT.md is the main continuity file.

The user should not manually rewrite it after each strategy.

Codex is responsible for updating local MASTER_CONTEXT.md after:

- rejected hypothesis;
- full backtest verdict;
- Monte Carlo audit;
- paper trading decision;
- major lesson;
- current phase change.

ChatGPT should remind the user to upload/replace the updated MASTER_CONTEXT.md in the ChatGPT Project after Codex updates it.

In each new Project chat, rely on:

1. Project instructions;
2. MASTER_CONTEXT.md;
3. uploaded rules/rejected/lesson files.

## Low Token Mode

Codex must operate in LOW TOKEN MODE by default. Canonical
definition: `.codex/AGENTS.md` Section 14. Summary:

- Read `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
  `obsidian/00_INDEX.md` (only when navigation is needed) ->
  targeted linked files only.
- Read MASTER_CONTEXT.md only when the task requires full handoff
  context; read this file only when project-level operating rules
  are needed.
- No full repo scans. No files > 5 MB without explicit user approval.
- Prefer `obsidian/wiki/` summaries over raw files. Do not read
  `results/raw/`, `data/`, or raw backtest artifacts by default.
- Short direct responses. One concrete next action. No long theory
  unless requested.
- Do not repeat known project context. Append logs; never
  overwrite history.
- Do not produce strategy code before research gates pass. Do not
  revive rejected hypotheses without new external evidence.
