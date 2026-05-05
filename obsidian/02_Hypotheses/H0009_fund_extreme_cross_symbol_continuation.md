---
id: H0009
slug: fund_extreme_cross_symbol_continuation
status: awaiting_audit
created: 2026-05-05
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
timeframe: 1h
profile: B-Position
execution_tier: M
direction: long
expected_trades_per_week: [2, 2]
event_horizon: h+72
free_parameters: [funding_extreme_event, hold_hours]
---

# H0009 - fund_extreme_cross_symbol_continuation

## 1. Mechanism

After a `FUND_EXTREME` event, extreme positive OR negative funding can
mark forced positioning pressure that clears the order book. In the
cited 3-year sample, forced liquidations cleared the order book and the
asset reverted toward the prevailing multi-month trend. The hypothesis
is always long after a `FUND_EXTREME` firing on BTCUSDT or ETHUSDT and
holds for the h+72 horizon.

## 2. Distinct-from-rejected statement

This is not H0001, H0003, H0004, or H0006 because it is not spot spread
reclaim, wick recovery, microtrend trailing, or Bollinger/range
mean-reversion. It is not H0002 because it does not use BTCUSDT to trade
ETHUSDT through residual lead-lag. It is not H0005 because it does not
trade a same-symbol compression breakout or generic price expansion. It
is not H0007 because it does not use the funding settlement clock or
bar-only pre-settlement displacement; it uses an actual funding extreme
state and a multi-day h+72 always-long recovery / trend-reversion
horizon. It is not H0008 because it does not combine funding with
premium compression to trade a crowding unwind; the proposed direction
is long regardless of funding sign.

## 3. Expected pre-fee edge

- Expected average pre-fee PnL per trade: BTCUSDT approximately 1.10
  percent; ETHUSDT approximately 0.98 percent.
- Reasoning: the cited 3-year split shows BTC FUND_EXTREME h+72:
  positive funding n=84 mean +1.61%, negative funding n=72 mean
  +0.50%, all n=156 mean +1.10%; ETH FUND_EXTREME h+72: positive
  funding n=77 mean +1.11%, negative funding n=59 mean +0.82%, all
  n=136 mean +0.98%. Both funding-sign branches went up, so this
  hypothesis is always long after FUND_EXTREME rather than trading in
  the sign of funding.
- Floor for the declared execution tier (see
  `obsidian/01_Rules/02_Fee_Slippage_Model.md`):
  - Tier T: must be >= 0.30 percent;
  - Tier M: must be >= 0.20 percent.
- Cited Data Layer evidence (path + quoted numeric line):
  - file: `data_layer/reports/summaries/research_candidates.md`
  - line: "| M | long | 1h | FUND_EXTREME | h+72 | 156 | +1.00% | 0.021 | 136 | +0.88% | 0.066 |"

## 3a. Stability evidence (walk-forward + permutation)

- direction: `long`. The cell appears in a Long section; this
  hypothesis implements that as always long after a `FUND_EXTREME`
  firing, regardless of whether funding is positive or negative.
- file: `data_layer/reports/summaries/walk_forward.md`
- T sign-stable: BTCUSDT `yes`; ETHUSDT `yes`.
- M sign-stable: BTCUSDT `yes`; ETHUSDT `yes`.
- file: `data_layer/reports/summaries/permutation_test.md`
- p-value: BTCUSDT `0.021`; ETHUSDT `0.066`. Both are <= 0.10 for Tier
  M.
- verdict: BTCUSDT `PASS`; ETHUSDT is `FAIL` under the report's Tier T
  p<=0.05 label but acceptable for Tier M because 0.066 <= 0.10.
- file: `data_layer/reports/summaries/research_candidates.md`
- section the cell appears in: "Cross-symbol Pareto + stability
  (highest grade)" with `tier=M` and `dir=long`; the component symbol
  rows also appear under "Tier M long candidates".
- horizon vs. profile: h+72 falls inside Profile B-Position allowed
  horizons h+24..h+168.

Quoted supporting rows:

```
| BTCUSDT | 1h | FUND_EXTREME | h+72 | 156 | +0.92% | +1.00% | yes | yes |
| ETHUSDT | 1h | FUND_EXTREME | h+72 | 136 | +0.80% | +0.88% | yes | yes |
| BTCUSDT | 1h | FUND_EXTREME | h+72 | 156 | +0.92% | +1.00% | 0.021 | PASS |
| ETHUSDT | 1h | FUND_EXTREME | h+72 | 136 | +0.80% | +0.88% | 0.066 | FAIL |
```

## 3b. Fee budget gate

Arithmetic from `obsidian/01_Rules/02_Fee_Slippage_Model.md`:

```
notional_per_trade  = starting_capital * margin_fraction * leverage
trades_per_year     = trades_per_week * 52
annual_friction     = trades_per_year * notional_per_trade * round_trip_friction
ratio               = annual_friction / starting_capital
```

Profile values used:
- starting_capital: 200
- margin_fraction: 0.5
- leverage: 2
- trades_per_week: 2
- round_trip_friction: 0.0008 (Tier M)

Result:

```
notional_per_trade  = 200 * 0.5 * 2 = 200
trades_per_year     = 2 * 52 = 104
annual_friction     = 104 * 200 * 0.0008 = 16.64
ratio               = 16.64 / 200 = 0.0832 = 8.32%
```

Result ratio: 0.0832, which is <= 0.25 and passes the fee budget gate.

Note: the 2 trades/week input is the actual approximate frequency from
the cited Data Layer counts and falls inside the Profile B-Position band
of 1 to 6 trades per week in `.codex/AGENTS.md` Section 3.

## 4. Expected trade frequency

- Per week per symbol (B-Position): BTCUSDT approximately 1.0 event per
  week; ETHUSDT approximately 0.9 events per week.
- Combined per week: approximately 1.87, rounded to 2 for the fee budget
  gate. This falls inside the Profile B-Position band of 1 to 6 trades
  per week in `.codex/AGENTS.md` Section 3.
- Per backtest window: BTCUSDT n=156 and ETHUSDT n=136 in the cited
  Data Layer evidence, 292 combined events over roughly 3 years.
- For B-Position, swing trade-count threshold is at least 30 completed
  trades; the cited event count should clear that threshold if
  implementation and fills preserve most events.

## 5. Free parameters

1. Name: `funding_extreme_event`.
   Role: use the Data Layer's pre-defined `FUND_EXTREME` event
   definition.
   Candidate value: `FUND_EXTREME`.
   Why this value is chosen a priori: it is the exact event row that
   appears in `research_candidates.md`, not a newly tuned threshold.

2. Name: `hold_hours`.
   Role: fixed exit horizon after entry.
   Candidate value: 72.
   Why this value is chosen a priori: h+72 is the cited horizon in the
   cross-symbol research candidate line.

## 6. Expected failure modes

1. The recovery/uptrend regime ends and the always-long
   post-FUND_EXTREME effect does not survive in an extended bear regime.
2. Funding payments over a 72-hour hold reduce or erase the net edge,
   especially when the strategy is on the paying side of funding.
3. Maker fills are adversely selected; the adverse-selection fill proxy
   admits trades only when subsequent price movement worsens entry
   quality.
4. BTCUSDT and ETHUSDT events overlap during the same market regimes,
   reducing diversification and increasing drawdown.
5. Custom funding data alignment in QuantConnect could be wrong or
   unavailable, blocking a valid test.

## 6a. Regime caveat

This signal was validated on a recovery / uptrend regime in the
2023-2026 sample, dominated by BTC/ETH recovery and continuation
behavior. If the prevailing trend reverses into an extended bear regime,
the always-long direction must be re-validated before relying on it.
After deployment or paper trading, monitor monthly post-event outcomes
by symbol and by funding sign to detect decay or sign reversal.

## 7. Data required

- What data is used? BTCUSDT and ETHUSDT Binance USD-M Futures 1h OHLC
  bars and historical funding-rate observations sufficient to reproduce
  the Data Layer `FUND_EXTREME` event.
- Is it available in QC Lean v17685 for BTCUSDT and ETHUSDT? Native
  historical funding-rate availability is not assumed. Local audited
  Tier 1 Binance funding-rate history exists in the Data Layer, but a
  QuantConnect implementation needs an approved custom-data path or
  explicit QC verification before engineering.
- If no: this hypothesis is blocked until an alternative source is
  approved.

## 8. Execution model

- Order type: maker limit entry and maker limit exit where possible,
  using the Tier M adverse-selection rule. No maker rebate is assumed.
- Entry bar / exit bar rule: compute the `FUND_EXTREME` event only from
  completed 1h data and funding values whose timestamps are known at or
  before the decision timestamp. Enter on the next executable bar after
  the signal. Exit after 72 hours unless a risk stop is hit first.
- No-leakage statement: the signal timestamp and all funding inputs must
  be strictly available before order submission. No same-bar close signal
  may execute at the same-bar close.

## 9. Success / failure definition

- Trade count over OOS window: >= 30 completed trades, using the swing
  branch for Profile B-Position.
- OOS Sharpe: > 1.0.
- OOS net average trade: > 0.
- Max drawdown: < 25 percent.
- Pre-fee average trade: >= 0.20 percent, using the Tier M floor for
  Profile B-Position.
- Win-rate / profit-factor: WR >= 50 percent in IS and OOS, OR PF >=
  1.25 with stable payoff ratio.
- Monte Carlo: only after the six pre-MC criteria pass; at least 1000
  trade-shuffle simulations and P5 of final equity > $200 starting
  capital.
- Failure: any single criterion above fails. No partial credit.
- Trade-count expectation over window: expected combined event count is
  approximately 292 over the 3-year Data Layer window before fill and
  overlap exclusions, above the swing minimum of 30.

## 10. Risk controls

- Position sizing rule: fixed fractional exposure with
  `margin_fraction=0.5`, `leverage=2`, isolated-margin assumption, and
  no leverage tuning.
- Hard stop rule: 20 percent project/session peak drawdown stop per the
  repository risk-control convention.
- Daily loss cap: no separate daily loss cap; this is a multi-day
  B-Position hypothesis and the hard drawdown stop is the primary
  portfolio-level risk control.

## 11. Maker tier specifics

Tier M requires the adverse-selection rule from
`obsidian/01_Rules/02_Fee_Slippage_Model.md`: a limit at price L is
treated as filled only if the bar reaches L and the next bar moves
further adverse to the fill side by at least 0.05 percent. Unfilled
entry limits should be cancelled rather than crossed to taker, because
this hypothesis is registered as Tier M and its fee budget uses Tier M
friction.

## 12. Exact next validation step

Invoke the pre-backtest auditor prompt on
`obsidian/02_Hypotheses/H0009_fund_extreme_cross_symbol_continuation.md`.

## 13. Links

- Candidate edge note: `obsidian/08_Data_Notes/CE0021_fund_extreme_cross_symbol_continuation.md`
- Strategy folder (after engineer): `strategies/H0009_fund_extreme_cross_symbol_continuation/`
- Backtest reports (after user run): `obsidian/04_Backtests/`
