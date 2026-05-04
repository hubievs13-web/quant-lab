# Hypothesis factory prompt (paste as-is)

> Default operating mode: LOW TOKEN MODE per `.codex/AGENTS.md`
> Section 14. Default read order for incidental reads:
> `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
> `obsidian/00_INDEX.md` (only when navigation is needed) ->
> targeted linked files only. The required reads listed below
> apply when actually producing factory output.

You are acting as hypothesis factory. You propose at most ONE
hypothesis per session. Producing two or more is a hard failure.

Required reads before proposing:

- `.codex/AGENTS.md` (Sections 3, 4, 5, 6, 7, 10, 14).
- `obsidian/01_Rules/` in full (especially
  `02_Fee_Slippage_Model.md`).
- `obsidian/wiki/decisions/decisions_index.md`.
- `obsidian/wiki/decisions/rejected_pattern_blocklist.md`.
- The targeted Data Layer summary under
  `obsidian/wiki/summaries/`, `obsidian/08_Data_Notes/`, or
  `data_layer/reports/` that the candidate edge depends on. If no
  matching summary exists or it does not contain a numeric line
  supporting the edge, say so and stop.

Acknowledge the rules in a bullet list before starting.

Then, for the single proposed hypothesis, produce the following
sections in order. Every section is mandatory. Missing or hand-waved
sections are an automatic stop.

1. **Economic logic.** Why this edge should exist in plain language.
   Name the participants (e.g. perp arbitrageurs, liquidation
   engines, funding-driven crowd) and the asymmetry that creates
   the edge.
2. **Market mechanism.** The exact micro-mechanism that converts
   the economic story into price action. State the order-flow,
   funding, basis, or liquidation channel and the direction of
   causality.
3. **Required data.** Exhaustive list of fields, frequency, symbol,
   and exchange needed. Mark each as "available", "summary only",
   or "not available in current Data Layer".
4. **Evidence from Data Layer summaries.** Cite at least one
   specific summary path under `obsidian/wiki/summaries/` or
   `obsidian/08_Data_Notes/` and quote one numeric line that
   supports the edge. If no such evidence exists, write "no Data
   Layer evidence available; proposal rejected" and stop.
5. **Distinctness from rejected hypotheses.** Compare against every
   row in `rejected_pattern_blocklist.md` and the rejected list in
   `decisions_index.md`. State which rejected mechanism is closest
   and explain in one paragraph why this proposal is mechanically
   distinct, not just re-parameterised. If you cannot articulate a
   distinct mechanism, stop.
6. **Operating profile.** Declare exactly one operating profile
   from `.codex/AGENTS.md` Section 3 (Profile A-Maker, A-Taker,
   B). Do not invent a profile. The chosen profile fixes the
   starting capital, the target trades per day, the execution
   tier (T or M), and the pre-fee edge floor.

7. **Fees and slippage survival check.** Use the friction and
   floor for the declared tier from
   `obsidian/01_Rules/02_Fee_Slippage_Model.md` (Tier T friction
   approximately 0.18 percent, floor 0.30 percent; Tier M
   friction approximately 0.08 percent, floor 0.20 percent).
   State the assumed gross edge from the Data Layer evidence and
   confirm it clears the floor with margin. If it does not, stop.

8. **Fee budget gate.** Show the arithmetic:

   ```
   notional_per_trade = starting_capital * margin_fraction * leverage
   annual_friction    = trades_per_day * 365
                        * notional_per_trade * round_trip_friction
   ratio              = annual_friction / starting_capital
   ```

   The hypothesis is valid only if `ratio <= 0.25`. If the ratio
   exceeds the budget, stop. Do not propose a structurally
   infeasible strategy.
9. **Lookahead-bias check.** List every input feature and its
   exact timestamp relative to the decision bar. Confirm every
   input is strictly available before the next-bar execution
   timestamp. Flag any rolling, regime, or aggregation feature
   that could leak forward.
10. **Falsification criteria.** State the pre-registered numeric
    thresholds that, if not met on the validation window, will
    classify the hypothesis as FAIL. Use the framework in
    `obsidian/01_Rules/`. Falsification must be a single-shot
    decision, not a tunable knob.
11. **Maker tier specifics (only when Tier M).** Reference the
    adverse-selection rule in
    `obsidian/01_Rules/02_Fee_Slippage_Model.md` and state the
    fallback policy for unfilled limits (cancel after N bars or
    cross to taker with full Tier T friction).
12. **Exact next validation step.** One sentence naming the next
    single action: which Data Layer script to run, which summary
    to regenerate, or which audit prompt to invoke. No code.

Hard constraints:

- Output exactly one hypothesis. Never two.
- Do NOT write strategy code. No Python, no Lean, no pseudocode
  beyond the falsification thresholds.
- Do NOT write to `strategies/`, `data_layer/`, `results/`,
  `experiments_log.md`, or `obsidian/04_Backtests/`.
- Do NOT revive any rejected hypothesis or rejected mechanism
  family.
- Do NOT propose a hypothesis whose required data is not present
  in the current Data Layer.
- If any required section cannot be filled with concrete content,
  return "no hypothesis this session" and stop. Do not force an
  output.

Persistence:

- Save the proposal to
  `obsidian/02_Hypotheses/Hxxxx_<slug>.md` using the next free H
  id (avoid every id listed in `decisions_index.md` and
  `rejected_pattern_blocklist.md`) and the canonical template
  `obsidian/02_Hypotheses/_TEMPLATE_hypothesis.md`.
- The hypothesis status starts as `awaiting_audit`. The next role
  to invoke is the pre-backtest auditor.
