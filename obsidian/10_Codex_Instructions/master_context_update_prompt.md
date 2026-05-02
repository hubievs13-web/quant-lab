# Codex Prompt — Update MASTER_CONTEXT.md

You are updating project continuity context.

Task:
Update MASTER_CONTEXT.md after the latest research-cycle event.

Before editing, read:

1. MASTER_CONTEXT.md
2. MASTER_CONTEXT_UPDATE_PROTOCOL.md
3. .codex/AGENTS.md
4. experiments_log.md
5. results/experiments.csv
6. relevant hypothesis note
7. relevant backtest report
8. relevant rejected/passed/post-mortem note
9. relevant lesson note, if any

Rules:

1. Keep MASTER_CONTEXT.md compact.
2. Do not paste full logs.
3. Do not paste screenshots.
4. Do not paste full source code.
5. Do not hide failed criteria.
6. Do not soften verdicts.
7. Do not tune failed strategies.
8. Do not change research conclusions without explicit ChatGPT verdict.

Update only relevant sections:

- Last updated
- Current status
- Current rejected hypotheses
- Current active hypothesis
- Latest result
- Key lessons
- Forbidden follow-ups
- Allowed next directions

After editing, output:

1. Files changed.
2. Sections of MASTER_CONTEXT.md changed.
3. Short summary of the new current status.
4. Reminder:
   “Upload the updated MASTER_CONTEXT.md to the ChatGPT Project, replacing the old one.”
5. Exact next prompt for ChatGPT Project.

Do not start a new research cycle.
Do not write strategy code.
Do not run backtests.
