# Rejected pattern blocklist

Compact list of mechanism families that have already been rejected
in this project. Any new hypothesis must be mechanically distinct
from every entry below. Do not revive these mechanisms by
re-parameterising or swapping symbols.

This file is a derived view. The canonical store is, in order of
authority:

1. file location (`obsidian/05_Rejected/` for rejected,
   `obsidian/06_Passed/` for passed);
2. `experiments_log.md` verdict lines;
3. `.codex/AGENTS.md` Section 10 rejected-mechanism table.

If this blocklist disagrees with any of the above, the canonical
store wins. Regenerate this file from `decisions_index.md` when a
new rejection is recorded.

## Status

- generated-at: 2026-05-03
- source: `obsidian/wiki/decisions/decisions_index.md` (rejected
  rows H0001 through H0007).
- supersedes: none.

## Blocklist (mechanism families)

Each row is a single rejected mechanism. Distinctness must be
argued at the mechanism level, not the parameter level.

| Family ID | Mechanism family | Class | Symbols / Tf | Source | Backtest evidence |
|---|---|---|---|---|---|
| F0001 | Spot spread reclaim mean reversion (H0001 ETH_spread_reclaim) | mean_reversion | ETHUSDC spot 1m | `decisions_index.md` (seed); `obsidian/05_Rejected/H0001_ETH_spread_reclaim.md` | none in vault (seed); requires verification before any reuse of this mechanism |
| F0002 | BTC perp / ETH lead-lag (H0002 btc_perp_eth_lag) | lead_lag | BTCUSDT / ETHUSDT 5m | `decisions_index.md`; `experiments_log.md` line 28 (2026-04-29 FAIL) | `obsidian/wiki/summaries/BT0001_H0002_2026-04-29.md` |
| F0003 | Liquidation wick mean reversion (H0003 SOL_liquidation_wick) | mean_reversion | SOLUSD spot 5m | `decisions_index.md` (seed); `obsidian/05_Rejected/H0003_SOL_liquidation_wick.md` | none in vault (seed); requires verification before any reuse of this mechanism |
| F0004 | Microtrend trailing momentum (H0004 BTC_microtrend_trailing) | momentum | BTCUSDT spot 1m | `decisions_index.md` (seed); `obsidian/05_Rejected/H0004_BTC_microtrend_trailing.md` | none in vault (seed); requires verification before any reuse of this mechanism |
| F0005 | Perp compression breakout / orderflow (H0005 perp_compression_breakout) | orderflow | BTCUSDT / ETHUSDT 5m | `decisions_index.md`; `experiments_log.md` line 29 (2026-04-29 FAIL) | `obsidian/wiki/summaries/H0005_smooth_blue_jellyfish_2026-04-29.md` |
| F0006 | Bollinger-band rejection mean reversion (H0006 BTC_BB_rejection_MR) | mean_reversion | BTCUSDT spot 5m | `decisions_index.md` (seed); `obsidian/05_Rejected/H0006_BTC_BB_rejection_MR.md` | none in vault (seed); requires verification before any reuse of this mechanism |
| F0007 | Funding settlement unwind (H0007 funding_settlement_unwind) | funding | BTCUSDT / ETHUSDT 5m | `decisions_index.md`; `experiments_log.md` line 30 (2026-05-01 FAIL) | folder never generated; see `obsidian/00_LINT_REPORT.md` Section 5 (Explained gaps); requires verification |

## Lessons that fold multiple families

- Spot, sub-5m, BTC / ETH / SOL mean-reversion and microtrend
  patterns (F0001, F0003, F0004, F0006) did not produce an edge
  after realistic costs. See `obsidian/07_Lessons/` (lesson
  L0001 referenced in `obsidian/00_INDEX.md`). Re-proposing any
  of these classes on the same venue and timeframe is forbidden
  without new external evidence.
- Funding-class mechanisms (F0007) have an existing rejection.
  Any new funding-class proposal must articulate distinction from
  F0007 per `.codex/AGENTS.md` Section 10.

## Forbidden follow-ups

- Do not re-propose any family above with new parameters,
  alternate symbol on the same venue, or alternate timeframe on
  the same venue.
- Do not relabel a rejected mechanism under a new name.
- A new hypothesis that touches any family above must explicitly
  cite the family ID and explain mechanical distinctness, or be
  REJECTED by the pre-backtest auditor.

## Update rule

- Regenerate from `decisions_index.md` only.
- Never change a verdict here. Verdicts are owned by the
  canonical store.
- When a new rejection is recorded, append a new family row.
  Never edit existing rows except to fix typos or to add a
  stronger evidence link.
