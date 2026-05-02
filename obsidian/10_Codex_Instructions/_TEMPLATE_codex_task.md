# Codex task instruction (per-task)

Copy this into the VS Code Codex chat when the canned role prompts in
this folder are not enough (for example when the task is a specific
cross-role question).

---

Role: researcher | engineer | auditor
Context files to read first:
- .codex/AGENTS.md
- .codex/roles/<role>.md
- obsidian/01_Rules/*
- obsidian/05_Rejected/*
- obsidian/07_Lessons/*
- <any specific hypothesis or strategy path>

Task:
<describe exactly what Codex should do>

Constraints recap:
- No tuning of failed strategies.
- Free parameters <= 3.
- Fee model: taker 0.04 percent per side, total round-trip friction
  approximately 0.18 percent.
- Pre-fee edge floor >= 0.10 percent per trade.
- No same-bar close-to-close execution.
- No emoji.
- Output format per role file.

Acknowledge rules in bullet list before starting.
