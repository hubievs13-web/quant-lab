# Engineer prompt (paste as-is, then replace Hxxxx_<slug>)

> Default operating mode: LOW TOKEN MODE per `.codex/AGENTS.md`
> Section 14. Default read order for incidental reads:
> `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
> `obsidian/00_INDEX.md` (only when navigation is needed) ->
> targeted linked files only. The required reads listed below
> apply when actually producing engineer output.

You are acting as engineer. Read .codex/AGENTS.md and
.codex/roles/engineer.md. Read obsidian/01_Rules/ in full. Read the
hypothesis at obsidian/02_Hypotheses/Hxxxx_<slug>.md and the candidate
edge note at obsidian/08_Data_Notes/CExxxx_<slug>.md if it exists.

Acknowledge the rules in a bullet list before starting.

Then:

1. Create strategies/Hxxxx_<slug>/ with:
   - main.py  (single-file QuantConnect Lean Python, paste-ready,
     Lean v17685 snake_case where canonical)
   - README.md (from
     obsidian/03_Strategies/_TEMPLATE_strategy_README.md, filled)
   - diagnostics.md (explicit list of metrics and logs to extract
     from QC)
2. Also create obsidian/03_Strategies/Sxxxx_<slug>.md as a short
   cross-reference.
3. Constraints:
   - Free parameters <= 3, declared at the top of main.py.
   - Fee model: custom fee 0.04 percent taker per side, slippage buffer
     so total round-trip friction is approximately 0.18 percent.
   - No data leakage. Next-bar execution on multi-asset signals.
   - Per-trade logs and daily summary logs.
   - Risk stop: hard flatten and stop for the session if drawdown from
     account peak exceeds 20 percent.
   - State the exact Binance Futures brokerage model assumption and
     provide a 3-day verification step in README.md.
4. Do NOT write to obsidian/04_Backtests/, obsidian/05_Rejected/,
   obsidian/06_Passed/ or experiments_log.md.
