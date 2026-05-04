# Engineer prompt (paste as-is, then replace Hxxxx_<slug>)

> Default operating mode: LOW TOKEN MODE per `.codex/AGENTS.md`
> Section 14. Default read order for incidental reads:
> `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
> `obsidian/00_INDEX.md` (only when navigation is needed) ->
> targeted linked files only. The required reads listed below
> apply when actually producing engineer output.

You are acting as engineer. Read `.codex/AGENTS.md` and
`.codex/roles/engineer.md`. Read `obsidian/01_Rules/` in full
(especially `02_Fee_Slippage_Model.md`). Read the hypothesis at
`obsidian/02_Hypotheses/Hxxxx_<slug>.md` and the candidate edge
note at `obsidian/08_Data_Notes/CExxxx_<slug>.md` if it exists.

Required hypothesis precondition: the pre-backtest auditor has
returned `VERDICT: ALLOW_ENGINEERING`. If the verdict is missing
or different, refuse and ask the user to rerun the auditor.

Acknowledge the rules in a bullet list before starting.

Then:

1. Create `strategies/Hxxxx_<slug>/` with:
   - `main.py`  (single-file QuantConnect Lean Python, paste-ready,
     Lean v17685 snake_case where canonical)
   - `README.md` (from
     `obsidian/03_Strategies/_TEMPLATE_strategy_README.md`, filled)
   - `diagnostics.md` (explicit list of metrics and logs to extract
     from QC)

2. Also create `obsidian/03_Strategies/Sxxxx_<slug>.md` as a
   short cross-reference.

3. Profile binding (mandatory):
   - The first line of `main.py` MUST be a comment of the form
     `# PROFILE: A-Maker` (or `A-Taker`, `B`, etc.) matching the
     hypothesis declaration.
   - The README MUST cite the same profile, the declared tier
     (T or M), the target trades per day, the expected pre-fee
     per-trade edge, and the fee budget gate arithmetic.

4. Code constraints:
   - Free parameters <= 3, declared at the top of `main.py` as
     module-level UPPER_SNAKE_CASE constants with type
     annotations.
   - Fee model: copy the canonical Tier T or Tier M fee model
     from `strategies/_lib/fee_models.py` and inline it into
     `main.py`. Do not import from `_lib` (QC web IDE is
     single-file). The inlined code MUST match `_lib` byte for
     byte except for class renaming.
   - Slippage / fill model:
     - Tier T: inline `BinanceUMTakerSlippageModel` from
       `strategies/_lib/slippage_models.py`.
     - Tier M: inline `BinanceUMMakerFillModel` from
       `strategies/_lib/maker_fill_proxy.py`. The
       adverse-selection rule MUST be present.
   - Risk controls: inline `DrawdownStop` from
     `strategies/_lib/risk_controls.py`. Hard stop at 20 percent
     drawdown from session peak.
   - Diagnostics: inline `PerTradeLogger` and `DailySummary`
     from `strategies/_lib/diagnostics.py`.
   - No data leakage. Next-bar execution on multi-asset signals.

5. Validate locally before declaring the strategy ready:
   - Run `python scripts/lint_strategy.py
     strategies/Hxxxx_<slug>/main.py`. The strategy is not
     considered ready unless the lint exits 0.
   - Paste the lint summary into the strategy README under a
     section titled `## Lint`.

6. Do NOT write to `obsidian/04_Backtests/`,
   `obsidian/05_Rejected/`, `obsidian/06_Passed/`, or
   `experiments_log.md`.
