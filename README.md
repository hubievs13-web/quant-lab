# quant-lab

Disciplined research loop for Binance USD-M Futures strategies against
QuantConnect (project 30774195, Lean v17685). Obsidian-first knowledge
base, Codex-driven code generation, manual QuantConnect backtesting,
strict falsification framework.

This repository is NOT a trading system. It is a research workbench.

## Structure

```
quant-lab/
  README.md                   # this file
  experiments_log.md          # append-only verdict log
  .codex/
    AGENTS.md                 # global operating rules for Codex
    README.md                 # how to use Codex in VS Code
    roles/
      researcher.md
      engineer.md
      auditor.md
  obsidian/                   # Obsidian vault root
    00_Index.md
    01_Rules/
      00_Hard_Rules.md
      01_Falsification_Framework_V3.md
      02_Fee_Slippage_Model.md
      03_No_Leakage_Checklist.md
      04_Monte_Carlo_Protocol.md
    02_Hypotheses/
      _TEMPLATE_hypothesis.md
    03_Strategies/
      _TEMPLATE_strategy_README.md
    04_Backtests/
      _TEMPLATE_backtest_report.md
    05_Rejected/
      _TEMPLATE_rejected_postmortem.md
      H0001_ETH_spread_reclaim.md
      H0003_SOL_liquidation_wick.md
      H0004_BTC_microtrend_trailing.md
      H0006_BTC_BB_rejection_MR.md
    06_Passed/
    07_Lessons/
      _TEMPLATE_lesson.md
      L0001_spot_below_5m_no_edge.md
    08_Data_Notes/
      _TEMPLATE_candidate_edge.md
      binance_futures_fees.md
      funding_rates.md
      open_interest.md
      liquidations_unavailable.md
    09_Daily_Logs/
      _TEMPLATE_daily_log.md
    10_Codex_Instructions/
      _TEMPLATE_codex_task.md
      researcher_prompt.md
      engineer_prompt.md
      auditor_prompt.md
  strategies/                 # code only; one folder per hypothesis
  research/                   # freeform scratch
  results/                    # machine-readable mirror of QC runs
    README.md
    experiments.csv           # one row per backtest run (upsert by backtest_id)
    raw/                      # raw QC export bundles, one folder per run
    trades/  orders/  logs/  reports/
  scripts/
    monte_carlo.py            # MC audit (post PRELIMINARY_PASS), draft verdict only
    process_qc_backtest.py    # raw QC export -> Obsidian report + experiments.csv
```

## Who does what

- User: runs QuantConnect backtests manually, collects results, asks
  the Devin chat for a verdict.
- Devin chat (external): owns the Falsification Framework and the
  verdict. Never writes code.
- Codex (in VS Code): reads `.codex/AGENTS.md` and the Obsidian vault.
  Three modes: researcher, engineer, auditor. Never logs into QC, never
  runs backtests, never issues verdicts.

See `.codex/README.md` and `.codex/AGENTS.md` for the full contract.

## Market assumptions (v1)

- Binance USD-M Futures.
- BTCUSDT, ETHUSDT. Shorts allowed. Leverage 2x-3x isolated.
- Timeframe 1m to 5m.
- Starting capital USD 200.
- 5 to 15 trades per day target.
- Fees: taker 0.04 percent per side; round-trip friction assumption
  approximately 0.18 percent.
- Pre-fee edge floor: 0.10 percent per trade.
- Data layer in v1: Obsidian-only markdown. No CSV / Parquet / DuckDB /
  SQLite. Any future data-layer proposal is a separate project phase.

## Lifecycle of a hypothesis

1. Codex researcher mode produces candidate edges + a hypothesis note.
2. User reviews in Obsidian.
3. Codex engineer mode produces `strategies/Hxxxx_<slug>/`.
4. Codex auditor mode (pre-backtest) checks hypothesis + code against
   every rule. Either CLEARED FOR BACKTEST or BLOCKED.
5. User pastes `main.py` into QC project 30774195, runs the backtest.
6. User drops raw exports into
   `results/raw/BTxxxx_Hxxxx_YYYY-MM-DD/` and runs
   `scripts/process_qc_backtest.py`. The script creates
   `obsidian/04_Backtests/BTxxxx_Hxxxx_YYYY-MM-DD/` with `report.md`,
   copies the raw files, and upserts `results/experiments.csv` with a
   draft verdict.
7. User sends `report.md` plus PRIMARY files (trades.csv, orders.csv,
   logs.txt, statistics.* if any) to the Devin chat. Screenshots are
   SECONDARY: attach if useful, never instead of primary.
8. Devin chat returns FAIL / INCONCLUSIVE / PRELIMINARY_PASS.
9. If PRELIMINARY_PASS, user runs `scripts/monte_carlo.py` on the
   trades export. The script accepts `pnl_pct` / `return_pct` /
   `pnl_percent` / `profit_pct` / `net_return_pct` and prints a draft
   MC verdict (PASS / FAIL / INCONCLUSIVE). Devin chat issues the
   final FINAL_PASS or FAIL.
10. Codex auditor mode (post-verdict) files the outcome in Obsidian and
    appends one line to `experiments_log.md`. Failed pre-backtest
    candidates go to `obsidian/05_Rejected/pre_backtest_rejected/`,
    not deleted.

## Evidence policy

- PRIMARY evidence: trades.csv, orders.csv, logs.txt, statistics.txt
  or statistics.json. Required for a high-confidence verdict.
- SECONDARY evidence: overview.png, equity_curve.png, report.pdf.
  Useful, never sufficient alone. Reports based on screenshots only
  are flagged `evidence_confidence: LOW_CONFIDENCE` and the Devin chat
  will not issue anything beyond INCONCLUSIVE on them.

## Non-negotiables

- No tuning of failed strategies.
- No "almost passed".
- No emoji.
- No fabricated data. UNKNOWN / MISSING are written explicitly.
- Files are never deleted. Failed pre-backtest hypotheses go to
  `obsidian/05_Rejected/pre_backtest_rejected/`. Failed post-backtest
  hypotheses go to `obsidian/05_Rejected/`. Both are permanent.
- Required reading of `obsidian/05_Rejected/` and `obsidian/07_Lessons/`
  before proposing a new hypothesis reduces the risk of repeated ideas
  but does not guarantee prevention. Every new hypothesis must include
  a distinct-from-rejected section.
- Final verdicts (PASS / FAIL / INCONCLUSIVE) come only from the Devin
  chat. Scripts and Codex roles produce DRAFT verdicts only.

## Low Token Mode

Agents operating on this repo (Codex, Devin chat, etc.) default
to LOW TOKEN MODE. Canonical definition: `.codex/AGENTS.md`
Section 14. Summary:

- Read `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
  `obsidian/00_INDEX.md` (only when navigation is needed) ->
  targeted linked files only.
- No full repo scans. No files > 5 MB without explicit user approval.
- Prefer `obsidian/wiki/` summaries over raw files. Do not read
  `results/raw/` or `data/` by default.
- Short direct responses. One concrete next action. No long theory
  unless requested.
- Do not produce strategy code before research gates pass. Do not
  revive rejected hypotheses without new external evidence.
- Append logs; never overwrite history.
