# Pareto Validation (after 5m -> 90 days)

Generated: 2026-05-03 UTC. Single pass; no tuning loops.

Source data: Binance BTCUSDT, 5m=90 days (25920 bars), 1h=180 days (4320 bars).
Round-trip fee+slippage proxy = 0.18% (taker). All cells use closed-bar features
and t+1 anchor (anti-lookahead).

## Decision

**WATCHLIST ONLY.**

The previous WATCHLIST candidate `EV_VOL_BREAKOUT 5m h+72` did **not** strengthen
with more data — it weakened. With n nearly doubled (48 -> 87), mean fwd halved
(+0.51% -> +0.24%), hit rate fell (69% -> 60%), and MFE/|MAE| degraded (1.30 ->
0.95, now unfavorable shape with median MAE bigger than median MFE).

| metric | n=48 (30d) | n=87 (90d) | rule |
|---|---|---|---|
| count | 48 | 87 | n>=80 met |
| mean fwd | +0.51% | +0.24% | net +0.06% after 0.18% fees |
| hit > 0 | 69% | 60% | >55% (cusp) |
| MFE / \|MAE\| | 1.30 | 0.95 | <1.0 unfavorable |

Net edge after fees +0.06% on n=87 is well within 1 SE of zero (per-trade std
~1.0%, SE of mean ~0.11%). The candidate is consistent with noise.

## All n>=80 cells, 5m timeframe

| event | h | n | mean fwd | hit | MFE | MAE | MFE/\|MAE\| | net after 0.18% |
|---|---|---|---|---|---|---|---|---|
| VOL_BREAKOUT | h+72 | 87 | +0.24% | 60% | +0.83% | -0.88% | 0.95 | +0.06% |
| PREMIUM_SPIKE | h+12 | 735 | +0.04% | 50% | +0.28% | -0.30% | 0.94 | -0.14% |
| PREMIUM_COMPRESSION | h+72 | 562 | +0.10% | 51% | +0.79% | -0.77% | 1.02 | -0.08% |
| FUNDING_WINDOW_PRE | h+12 | 264 | +0.03% | 53% | +0.28% | -0.26% | 1.10 | -0.15% |
| PREMIUM_COMPRESSION | h+3 | 563 | +0.02% | 53% | +0.15% | -0.13% | 1.14 | -0.16% |
| FUNDING_WINDOW_PRE | h+3 | 264 | -0.01% | 55% | +0.13% | -0.12% | 1.06 | -0.19% |

No 5m cell with n>=80 produces a net-positive edge that comfortably exceeds the
0.18% friction proxy. The closest is VOL_BREAKOUT h+72 at +0.06% — within noise.

## Why no RESEARCH CANDIDATE yet

1. **Sample size resolved a small-sample illusion.** The previous +0.51% mean on
   n=48 collapsed to +0.24% on n=87. The original signal was likely an artifact
   of the April-2026 regime; the Feb–Mar window has different vol-breakout
   dynamics.
2. **MFE/|MAE| flipped unfavorable** (1.30 -> 0.95). With median MAE > median
   MFE, even a working entry has below-even drawdown vs reward profile.
3. **Net edge after fees is statistically indistinguishable from zero.**
4. Premium events (large n) still hover near or below the friction line.

## Why not "NO CANDIDATE"

Some weak-but-positive signal remains in:
- VOL_BREAKOUT 5m h+72 (+0.06% net, n=87) — keep on watchlist; revisit if
  history extends to ~180d for 5m.
- 1h-side direction effects: VOL_BREAKOUT 1h h+1 / h+3 are persistently
  *negative* (-0.25%, -0.54%); flagging this as a possible short-side cue
  is more honest than calling vol-breakout "long-only".

## Recommended next action

Stop pursuing VOL_BREAKOUT 5m h+72 as a long-only candidate; it is more likely
noise than edge after this expansion. Two cleaner next steps:

1. **Cross-exchange validation (Phase 5)**: ingest Bybit + OKX BTCUSDT 5m/1h
   and check whether `EV_PREMIUM_SPIKE` and `EV_PREMIUM_COMPRESSION` fire at
   similar timestamps with similar forward returns. If yes, the after-fees gap
   may close via signal averaging across exchanges.
2. **Direction split for VOL_BREAKOUT**: separate fires by sign of `ret_3` (or
   `slope_ret_24`) at the entry bar; the 1h-side negative cells suggest the
   event-level mean hides two sub-populations.

## Constraints honored

- One file modified (this report). No bulk data committed; `data_layer/store/`
  stays gitignored. No hypothesis generated. No strategy code touched. No
  Bybit/OKX ingest; no ETHUSDT.
