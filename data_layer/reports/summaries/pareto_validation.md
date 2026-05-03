# Pareto Validation (one-shot)

Generated: 2026-05-03 UTC. Single pass; no tuning loops.

Source data: Binance BTCUSDT, 5m=30 days (8640 bars), 1h=180 days (4320 bars).
Methodology: re-detect events under each variant, rebuild outcomes, aggregate
leaderboard. Compare cells with n>=30 only. Round-trip fee+slippage proxy = 0.18%.

## Decision

**WATCHLIST ONLY.**

Best candidate is `EV_VOL_BREAKOUT` 5m h+72 — but n=48 fails the n>=50 floor and
1h-side is sign-flipped, breaking the stability rule.

| event | tf | h | n | mean fwd | hit | MFE / \|MAE\| | sharpe | net after 0.18% |
|---|---|---|---|---|---|---|---|---|
| VOL_BREAKOUT | 5m | h+72 | 48 | +0.51% | 69% | 1.30 | 0.37 | +0.33% |
| PREMIUM_SPIKE | 5m | h+72 | 241 | +0.20% | 61% | 1.36 | 0.19 | +0.02% |
| PREMIUM_COMPRESSION | 1h | h+3 | 71 | +0.15% | 59% | 1.10 | 0.20 | -0.03% |
| PREMIUM_SPIKE | 1h | h+3 | 131 | +0.16% | 58% | 1.50 | 0.16 | -0.02% |
| FUND_FLIP | 1h | h+24 | 75 | +0.32% | 49% | 1.13 | 0.14 | +0.13% |

Notes per cell:
- VOL_BREAKOUT 5m h+72: n=48 (just under 50), 1h-side h+3 is -0.54% (n=34) →
  inconsistent across timeframes; cannot promote.
- PREMIUM_SPIKE 5m h+72: n=241 (large), but net edge collapses to ~0% after
  fees; mean is too small for a 6-hour holding period.
- PREMIUM_COMPRESSION 1h h+3 / PREMIUM_SPIKE 1h h+3: positive raw mean, but net
  edge after fees is negative.
- FUND_FLIP 1h h+24: hit rate 49% < 55% → fails decision rule.

## Sensitivity check (one pass)

| variant | top cell | n | mean fwd | hit | sharpe |
|---|---|---|---|---|---|
| baseline | VOL_BREAKOUT 5m h+72 | 48 | +0.51% | 69% | 0.37 |
| strict_premium (z >= 3) | (no premium cell with n>=30) | - | - | - | - |
| strict_vol_breakout (pctile=99.5) | VOL_BREAKOUT 5m h+72 | 28 | +0.61% | 68% | 0.42 |

- `strict_premium` drops every PREMIUM cell below n=30 (5m PREMIUM_SPIKE 244→29,
  1h 131→18). Reduces tradable sample without lifting sharpe meaningfully.
- `strict_vol_breakout` lifts the 5m h+72 mean a bit (+0.51 → +0.61%) but every
  cell drops below n=30. The cleaner signal does not justify losing sample.
- **No threshold change is justified.** `events.yaml` left as-is.

## Why no RESEARCH CANDIDATE yet

1. The only cell with high enough hit rate and MFE-favourable shape
   (`VOL_BREAKOUT 5m h+72`) has n=48, missing the n>=50 hurdle.
2. That cell does not generalise: 1h h+3 is -0.54% mean (n=34), 1h h+1 is
   -0.25% (n=34). Net direction is timeframe-dependent.
3. Premium events have plenty of samples but raw mean fwd is in the same
   order-of-magnitude as the assumed 0.18% friction, so net edge is
   indistinguishable from zero after costs.
4. Stricter thresholds shrink sample size faster than they raise sharpe.

## Watchlist (track, do not trade)

- `EV_VOL_BREAKOUT` 5m h+72: revisit once 5m history reaches >=60d (sample
  should comfortably clear n>=50 with similar hit rate).
- `EV_PREMIUM_SPIKE` 1h h+3: revisit on cross-exchange (Bybit / OKX); if the
  same sign appears with comparable hit rate, the after-fees edge becomes
  more credible via portfolio averaging.
- `EV_FUND_FLIP` 1h h+24: revisit once 1h history reaches >=365d (n grows
  linearly with window).

## Recommended next action

Extend Binance 5m history to ~60-90 days (cheap, same CDN source) **before**
spending the cost of Phase 5 cross-exchange ingest. If `EV_VOL_BREAKOUT` 5m h+72
holds n>=80 with hit>=60% and net after fees still > +0.20%, it earns
RESEARCH CANDIDATE status. Otherwise, re-evaluate.

Hard caveats: this is a descriptive scan, not a verdict. No hypothesis is
created. No strategy code is touched.
