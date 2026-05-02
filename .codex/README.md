# .codex/README.md

How to operate Codex inside VS Code for this repository.

Codex runs as a VS Code extension (GitHub Copilot Chat or ChatGPT). It has
full filesystem write access to this workspace and can execute Python
locally. It does NOT have access to QuantConnect. The user runs backtests
manually in QuantConnect project 30774195.

---

## Golden rules before every session

1. Open this repo as the active VS Code workspace.
2. Make sure Codex can see `.codex/AGENTS.md`. Pin it in the chat context
   if the extension allows.
3. Start every Codex session with the exact sentence:
   "Read .codex/AGENTS.md and .codex/roles/<role>.md. Then read
   obsidian/01_Rules/ and obsidian/05_Rejected/. Do not start the task
   until you have acknowledged the rules in a bullet list."
4. If Codex skips the acknowledgement, stop and re-prompt.
5. Never ask Codex to "fix" or "improve" a failed strategy. A failed
   strategy is rejected. If you want another try, the mechanism must
   change.

---

## Three modes

Codex operates in exactly three modes. Never mix them in one prompt.

### Researcher mode

Purpose: generate candidate edges for Binance USD-M Futures, pick one,
and write a hypothesis note.

Prompt template:

```
You are acting as researcher. Read .codex/AGENTS.md and
.codex/roles/researcher.md. Read all files under obsidian/01_Rules/ and
obsidian/05_Rejected/. Then:

1. Produce up to 5 candidate edges using the candidate edge template
   (obsidian/08_Data_Notes/_TEMPLATE_candidate_edge.md). Save each to
   obsidian/08_Data_Notes/CExxxx_<slug>.md.
2. Rank them.
3. Select one and produce obsidian/02_Hypotheses/Hxxxx_<slug>.md using
   the hypothesis template. Use the next free Hxxxx id (H0002, H0005,
   H0007, ... are free; skip H0001/H0003/H0004/H0006).
4. Do not write strategy code in this mode.
```

After researcher finishes: user reviews the hypothesis note in Obsidian.
If the mechanism is distinct from H0001/H0003/H0004/H0006 and the
hypothesis template is fully filled, move to engineer mode.

### Engineer mode

Purpose: turn a specific hypothesis into a paste-ready QuantConnect Lean
Python strategy with a README and a diagnostics plan.

Prompt template:

```
You are acting as engineer. Read .codex/AGENTS.md and
.codex/roles/engineer.md. Read the hypothesis at
obsidian/02_Hypotheses/Hxxxx_<slug>.md. Read all files under
obsidian/01_Rules/.

1. Create strategies/Hxxxx_<slug>/ with:
   - main.py  (single-file QuantConnect Lean Python, paste-ready)
   - README.md (strategy README template, filled)
   - diagnostics.md (diagnostics plan template, filled)
2. Use snake_case where Lean v17685 supports it.
3. Explicit fee and slippage model per AGENTS.md section 4.
4. Free parameters <= 3, enumerated at the top of main.py.
5. No data leakage. Next-bar execution on any multi-asset signal.
6. Include enough logs for later diagnostics. Log every trade with
   reason code, entry price, exit price, holding bars, pre-fee PnL,
   post-fee PnL.
7. Do not write to obsidian/04_Backtests/, obsidian/05_Rejected/,
   obsidian/06_Passed/ or experiments_log.md.
```

After engineer finishes: user opens `strategies/Hxxxx_<slug>/main.py`,
pastes into QuantConnect project 30774195, runs the backtest.

### Auditor mode

Purpose: review hypothesis + code BEFORE the user runs the backtest, and
AFTER the Devin verdict, record the post-mortem in Obsidian.

Prompt template (pre-run audit):

```
You are acting as auditor. Read .codex/AGENTS.md and
.codex/roles/auditor.md. Read obsidian/02_Hypotheses/Hxxxx_<slug>.md and
strategies/Hxxxx_<slug>/.

Produce an audit report in the VS Code chat only. Do not write to
Obsidian. Check the hypothesis and code against every rule in
AGENTS.md sections 4, 5, 6, 7. Output:

1. Checklist with pass/fail per rule.
2. Blocking issues, if any.
3. Explicit statement: CLEARED FOR BACKTEST or BLOCKED.

Do not produce a verdict on the hypothesis itself. The Devin chat owns
the verdict.
```

Prompt template (post-verdict recording):

```
You are acting as auditor. Read the Devin verdict pasted below. Copy
the hypothesis file appropriately:

- If FAIL: move obsidian/02_Hypotheses/Hxxxx_<slug>.md to
  obsidian/05_Rejected/Hxxxx_<slug>.md and append a post-mortem using
  _TEMPLATE_rejected_postmortem.md. Do not edit the original
  hypothesis content; add a Post-mortem section at the bottom.
- If PRELIMINARY PASS or FINAL PASS: leave the hypothesis in place and
  create obsidian/04_Backtests/BTxxxx_Hxxxx_YYYY-MM-DD.md using the
  backtest report template with the Devin verdict and notes.
- If FINAL PASS only: additionally move Hxxxx to obsidian/06_Passed/.

Also append a line to experiments_log.md with ID, date, verdict, key
metrics.

Do not tune parameters under any circumstances.

Devin verdict:
<paste>
```

---

## How to pass results back to Devin

After the user runs the backtest in QuantConnect:

1. Export from QC into `results/raw/BTxxxx_Hxxxx_YYYY-MM-DD/`:
   - PRIMARY (required for a high-confidence verdict):
     - trades.csv
     - orders.csv
     - logs.txt
     - statistics.txt or statistics.json (if available)
   - SECONDARY (helpful, not sufficient alone):
     - overview.png
     - equity_curve.png
     - report.pdf (if exported)
2. Run:
   ```
   python scripts/process_qc_backtest.py \
       --hypothesis Hxxxx --strategy Sxxxx \
       --raw-dir results/raw/BTxxxx_Hxxxx_YYYY-MM-DD \
       --symbols BTCUSDT,ETHUSDT --timeframe 1m \
       --is-window IS_START:IS_END --oos-window OOS_START:OOS_END
   ```
   This creates `obsidian/04_Backtests/BTxxxx_Hxxxx_YYYY-MM-DD/` with
   `report.md` and copies of the raw files, and upserts a row in
   `results/experiments.csv` with `verdict` set to a DRAFT value
   (FAIL_DRAFT / INCONCLUSIVE_DRAFT / READY_FOR_DEVIN_REVIEW).
3. In the Devin chat, paste:
   - Hypothesis ID.
   - Strategy ID.
   - Full `report.md` content.
   - PRIMARY files attached (trades.csv, orders.csv, logs.txt, and
     statistics if available). Screenshots are SECONDARY; attach only
     if asked or if you want the Devin chat to sanity-check the equity
     curve.
4. Wait for the Devin verdict. Do not run Codex auditor until the
   verdict is in.

Evidence confidence rule:

- If only screenshots are available, the report is marked
  `evidence_confidence: LOW_CONFIDENCE` and the Devin chat will not
  issue anything beyond INCONCLUSIVE. Re-export the missing primary
  files from QC and rerun the script.

## Monte Carlo (after PRELIMINARY_PASS only)

When the Devin chat returns PRELIMINARY_PASS, the user runs:

```
python scripts/monte_carlo.py results/raw/BTxxxx_Hxxxx_YYYY-MM-DD/trades.csv \
    --mode bootstrap --sims 1000 --start 200 --min-trades 300
```

The script needs a column named `pnl_pct` (preferred) or one of
`return_pct`, `pnl_percent`, `profit_pct`, `net_return_pct` containing
per-trade post-fee return in percent. If the column is missing, the
script prints a clear error listing the columns it found; rename or
add the column upstream rather than letting the script guess.

The script outputs a `verdict_draft` (PASS / FAIL / INCONCLUSIVE)
based on:

- P5(final equity) > start
- P95(max drawdown) < 25 percent  (worse-tail percentile for drawdown)
- P(final < start) < 5 percent
- trade_count >= --min-trades (else INCONCLUSIVE)

Exit codes from `monte_carlo.py`:

- 0  PASS
- 1  FAIL
- 2  INPUT_ERROR (bad CSV column, unreadable file)
- 3  INCONCLUSIVE

Paste the script output into the Monte Carlo section of `report.md`
and send back to the Devin chat for the FINAL_PASS / FAIL decision.

---

## How to avoid accidental curve-fitting

- Never paste "the backtest failed, try X instead" into Codex. That is
  tuning. File a new hypothesis note with a new mechanism.
- Never change a parameter in a rejected strategy and rerun. That is a
  new hypothesis; it must go through the full researcher -> engineer ->
  auditor cycle.
- If you feel pressure to force a PASS, stop the session and re-read
  `obsidian/01_Rules/00_Hard_Rules.md`.
- Keep `obsidian/05_Rejected/` in Codex's read context at all times. It
  is the permanent memory of what did not work.

---

## Quick reference

- AGENTS.md: `.codex/AGENTS.md`.
- Roles: `.codex/roles/{researcher,engineer,auditor}.md`.
- Rules: `obsidian/01_Rules/`.
- Templates: `obsidian/*/_TEMPLATE_*.md`.
- Rejected: `obsidian/05_Rejected/`.
- Strategies on disk: `strategies/<HypothesisID>_<slug>/`.
- Process QC backtest: `scripts/process_qc_backtest.py`.
- Monte Carlo script: `scripts/monte_carlo.py`.
- Experiments table: `results/experiments.csv`.
