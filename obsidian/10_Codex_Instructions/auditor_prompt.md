# Auditor prompts (paste as-is)

> Default operating mode: LOW TOKEN MODE per `.codex/AGENTS.md`
> Section 14. Default read order for incidental reads:
> `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
> `obsidian/00_INDEX.md` (only when navigation is needed) ->
> targeted linked files only. The required reads listed in each
> sub-mode below apply when actually producing auditor output.

Two modes. Pick one per session. Never both.

---

## A. Pre-backtest audit

You are acting as auditor. Read .codex/AGENTS.md and
.codex/roles/auditor.md. Read obsidian/01_Rules/ in full. Read
obsidian/02_Hypotheses/Hxxxx_<slug>.md and
strategies/Hxxxx_<slug>/ (main.py, README.md, diagnostics.md).

Acknowledge the rules in a bullet list before starting.

Produce an audit report in the VS Code chat only. Do NOT write to
Obsidian. Check against every rule in AGENTS.md sections 4, 5, 6, 7.
Output:

1. Hypothesis review checklist (pass/fail per item).
2. Code review checklist (pass/fail per item).
3. Blocking issues, if any.
4. Explicit final line: CLEARED FOR BACKTEST or BLOCKED.

Do not produce a verdict on the hypothesis itself.

---

## B. Post-verdict recording

You are acting as auditor. Read .codex/AGENTS.md and
.codex/roles/auditor.md. The Devin chat has issued the verdict below.

Acknowledge the rules in a bullet list before starting.

Then:

- Append one line to experiments_log.md:
  YYYY-MM-DD | Hxxxx | <verdict> | trade_count | sharpe | avg_trade_net | max_dd | notes
- If verdict is FAIL:
  - Move obsidian/02_Hypotheses/Hxxxx_<slug>.md to
    obsidian/05_Rejected/Hxxxx_<slug>.md.
  - Append a Post-mortem section using
    obsidian/05_Rejected/_TEMPLATE_rejected_postmortem.md.
  - Do NOT edit the original hypothesis body.
  - If a generalizable lesson exists, create
    obsidian/07_Lessons/Lxxxx_<slug>.md.
- If verdict is INCONCLUSIVE:
  - Leave hypothesis in place.
  - Ensure the backtest report exists at
    obsidian/04_Backtests/BTxxxx_Hxxxx_YYYY-MM-DD.md with reasoning
    for why evidence is insufficient.
- If verdict is PRELIMINARY_PASS:
  - Leave hypothesis in place. Mark backtest report
    verdict: PRELIMINARY_PASS. Note Monte Carlo pending.
- If verdict is FINAL_PASS:
  - Move hypothesis to obsidian/06_Passed/Hxxxx_<slug>.md.
  - Mark backtest report verdict: FINAL_PASS and attach MC summary.

Never tune. Never rename to hide history. Never edit rejected bodies.

Devin verdict:
<paste verdict block here>
