# 00_Index

Entry point of the Obsidian vault. Open this file first.

## Folders

- `01_Rules/` — hard rules, falsification framework, fee/slippage model,
  no-leakage checklist, Monte Carlo protocol. Immutable without explicit
  user approval.
- `02_Hypotheses/` — active hypotheses. One file per hypothesis. Created
  by researcher mode. Moved to `05_Rejected/` or `06_Passed/` after
  verdict.
- `03_Strategies/` — short cross-reference notes linking hypothesis
  notes to the code folder under `strategies/`.
- `04_Backtests/` — one note per backtest run. Filled by the user with
  QC results and by auditor mode after Devin verdict.
- `05_Rejected/` — permanent graveyard. Never edited to look better.
  Codex must read this before proposing any new hypothesis.
- `06_Passed/` — hypotheses that cleared the full framework including
  Monte Carlo. Rare by design.
- `07_Lessons/` — generalizable lessons learned from rejected or
  inconclusive experiments. Not per-hypothesis detail.
- `08_Data_Notes/` — candidate edge notes, data availability notes (what
  is reliably available in QC Lean v17685 for Binance USD-M Futures,
  what is not, what is forbidden because it cannot be fabricated).
- `09_Daily_Logs/` — short daily research log. One file per calendar
  day.
- `10_Codex_Instructions/` — canned prompts for Codex modes and a
  per-task template for when you want to send a specific instruction to
  Codex that is larger than one sentence.

## ID scheme

- Hypothesis: `Hxxxx` (zero-padded, 4 digits). Next free IDs: H0002,
  H0005, H0007, H0008, ...
- Strategy cross-ref: `Sxxxx` — reuses the hypothesis number.
- Backtest report: `BTxxxx`.
- Candidate edge: `CExxxx`.
- Lesson: `Lxxxx`.

## Current state (seed)

- Rejected: H0001, H0003, H0004, H0006. See `05_Rejected/`.
- Lesson L0001: spot <=5m BTC/ETH/SOL mean-reversion and microtrend
  patterns did not produce an edge after realistic costs.

## Read order for Codex

1. `../.codex/AGENTS.md`
2. Everything in `01_Rules/`
3. Everything in `05_Rejected/`
4. `07_Lessons/`
5. `08_Data_Notes/`
