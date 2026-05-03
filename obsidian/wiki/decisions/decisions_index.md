# Decisions index (rejected + active)

Read-only mirror of hypothesis status. Derived from canonical
files. Never sets status.

The canonical store is, in order of authority:

1. file location (`obsidian/02_Hypotheses/` = active,
   `obsidian/05_Rejected/` = rejected,
   `obsidian/06_Passed/` = passed);
2. `experiments_log.md` verdict lines;
3. `.codex/AGENTS.md` Section 10 rejected-mechanism table.

If this index disagrees with any of the above, the canonical store
wins.

## Status

- generated-at: 2026-05-02
- supersedes: none
- regenerate-trigger: any new hypothesis verdict, or new entry in
  `obsidian/02_Hypotheses/`, `05_Rejected/`, or `06_Passed/`.

## Rejected hypotheses (do not revive without new external evidence)

| ID | Slug | Class | Symbols / Tf | Verdict source | Backtest evidence |
|---|---|---|---|---|---|
| H0001 | ETH_spread_reclaim | mean_reversion | ETHUSDC spot 1m | `experiments_log.md` line 14 (seed) | none in vault (seed) |
| H0002 | btc_perp_eth_lag | lead_lag | BTCUSDT/ETHUSDT 5m | `experiments_log.md` line 28 (2026-04-29 FAIL) | `obsidian/wiki/summaries/BT0001_H0002_2026-04-29.md` |
| H0003 | SOL_liquidation_wick | mean_reversion | SOLUSD spot 5m | `experiments_log.md` line 15 (seed) | none in vault (seed) |
| H0004 | BTC_microtrend_trailing | momentum | BTCUSDT spot 1m | `experiments_log.md` line 16 (seed) | none in vault (seed) |
| H0005 | perp_compression_breakout | orderflow | BTCUSDT/ETHUSDT 5m | `experiments_log.md` line 29 (2026-04-29 FAIL) | `obsidian/wiki/summaries/H0005_smooth_blue_jellyfish_2026-04-29.md` |
| H0006 | BTC_BB_rejection_MR | mean_reversion | BTCUSDT spot 5m | `experiments_log.md` line 17 (seed) | none in vault (seed) |
| H0007 | funding_settlement_unwind | funding | BTCUSDT/ETHUSDT 5m | `experiments_log.md` line 30 (2026-05-01 FAIL) | folder never generated; see `obsidian/00_LINT_REPORT.md` Section 5 (Explained gaps) |

All seven canonical files live under `obsidian/05_Rejected/Hxxxx_*.md`
with frontmatter `status: rejected`. Frontmatter alignment was done
in PR #7 (H0002 / H0005 / H0007).

## Forbidden follow-ups

Any new researcher-mode hypothesis must explicitly explain how it
is **mechanically distinct** from the seven rejected mechanisms
above per `.codex/AGENTS.md` Section 10. Do not re-propose the
same mechanism with new parameters or an alternate symbol.

## Active hypotheses

| ID | Slug | Class | Symbols / Tf | Status | Strategy package | Notes |
|---|---|---|---|---|---|---|
| H0008 | funding_premium_crowding_unwind | funding | BTCUSDT/ETHUSDT 5m | `awaiting_audit` (set in PR #8) | `strategies/H0008_funding_premium_crowding_unwind/` complete (README, main.py, diagnostics, custom_data_smoke); cross-ref note `obsidian/03_Strategies/S0008_*.md` | no backtest run yet; audit pending; no verdict in `experiments_log.md` |

The `funding` mechanism class is shared with H0007. The H0008
hypothesis note must articulate distinction from H0007 before any
full backtest is approved (see `.codex/AGENTS.md` Section 10).

## Passed hypotheses

None. `obsidian/06_Passed/` is empty.

## Update rule

- Regenerate this page from canonical files only.
- Never edit it to override the canonical store.
- If a new verdict is added to `experiments_log.md`, append a row
  here in the next batch update; do not edit existing rows.
