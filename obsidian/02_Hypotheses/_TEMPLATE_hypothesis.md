---
id: Hxxxx
slug: short_slug
status: draft   # draft | active | rejected | preliminary_pass | final_pass
created: YYYY-MM-DD
mechanism_class: funding | oi | basis | lead_lag | orderflow | other
symbols: [BTCUSDT, ETHUSDT]
timeframe: 1m | 5m
profile: A-Maker | A-Taker | B-Position | B   # one of `.codex/AGENTS.md` Section 3 profiles
execution_tier: M | T            # M for maker (limit + adverse-selection), T for taker (market)
direction: long | fade           # long trades the event direction; fade trades against it
expected_trades_per_day: [low, high]   # for A-Maker / A-Taker / B
expected_trades_per_week: [low, high]  # for B-Position (omit the per-day field)
event_horizon: h+N               # one of h+1..h+12 for intraday profiles, h+24..h+168 for B-Position
free_parameters: [p1_name, p2_name, p3_name]   # at most 3
---

# Hxxxx — short_slug

## 1. Mechanism

Describe the economic or microstructural reason this edge should exist.
Two to four sentences.

## 2. Distinct-from-rejected statement

One paragraph showing this is not a restatement of H0001, H0003, H0004,
or H0006. Name the specific difference in mechanism, not in parameter
values.

## 3. Expected pre-fee edge

- Expected average pre-fee PnL per trade: X.XX percent.
- Reasoning: ...
- Floor for the declared execution tier (see
  `obsidian/01_Rules/02_Fee_Slippage_Model.md`):
  - Tier T: must be >= 0.30 percent;
  - Tier M: must be >= 0.20 percent.
- Cited Data Layer evidence (path + quoted numeric line):
  - file: `data_layer/reports/...`
  - line: "..."

## 3a. Stability evidence (walk-forward + permutation)

Quote two specific numbers tied to the same (symbol, timeframe,
event_type, horizon) cell as the leaderboard citation above. If
either report does not contain the cell, the hypothesis is below
the n>=80 stability threshold and cannot pass the auditor.

- direction: `long` or `fade`. `long` trades in the event
  direction and requires `full_mean > friction` (the cell appears
  in a Long section of `research_candidates.md`). `fade` trades
  against the event and requires `full_mean < -friction` (the
  cell appears in a Fade section). Cells with small negative
  `full_net` but `|mean| < friction` are NOT in any section and
  cannot be cited.
- file: `data_layer/reports/summaries/walk_forward.md`
- T sign-stable: ... (must be `yes` for Tier T, regardless of
  direction)
- M sign-stable: ... (must be `yes` for Tier M, regardless of
  direction)
- file: `data_layer/reports/summaries/permutation_test.md`
- p-value: ... (Tier T requires `<= 0.05`, Tier M requires
  `<= 0.10`; the Tier M threshold is kept slightly looser than
  Tier T because maker friction is lower, not because of sample
  size)
- verdict: ... (must be `PASS` for Tier T)
- file: `data_layer/reports/summaries/research_candidates.md`
- section the cell appears in: ... (must match the declared
  direction and tier; e.g. "Tier M long candidates" for a
  Profile A-Maker or B-Position long, or "Tier M fade
  candidates" for a Profile A-Maker fade.)
- horizon vs. profile: state the cited cell's `h+N` horizon and
  confirm it falls in the declared profile's allowed range
  (Profile A-Maker / A-Taker / B: `h+1`..`h+12`; Profile
  B-Position: `h+24`..`h+168`).

## 3b. Fee budget gate

Show the arithmetic from
`obsidian/01_Rules/02_Fee_Slippage_Model.md`:

```
notional_per_trade  = starting_capital * margin_fraction * leverage
trades_per_year     = trades_per_day * 365      # A-Maker / A-Taker / B
                    = trades_per_week * 52      # B-Position
annual_friction     = trades_per_year * notional_per_trade * round_trip_friction
ratio               = annual_friction / starting_capital
```

Profile values used:
- starting_capital: ...
- margin_fraction: ...
- leverage: ...
- trades_per_day: ...   (omit for B-Position)
- trades_per_week: ...  (omit for non-B-Position)
- round_trip_friction: 0.0018 (Tier T) or 0.0008 (Tier M)

Result ratio: ... (must be <= 0.25 to pass).

## 4. Expected trade frequency

- Per day per symbol (A-Maker / A-Taker / B): ...
- Per week per symbol (B-Position): ...
- Per backtest window: ...
- Must plausibly reach >= 300 trades over the OOS window to satisfy
  criterion 1 of the framework. For B-Position this typically requires
  a 3-year backtest (5 trades/week * 52 weeks * 2 symbols ~= 520
  trades; 15 trades/week ~= 1560 trades).

## 5. Free parameters

List exactly the 3 (or fewer) parameters. For each:

- Name.
- Role.
- Candidate value.
- Why this value is chosen a priori (not post hoc).

## 6. Expected failure modes

Enumerate at least 3 specific ways this edge can fail. Do not write
"market regime change" alone. Be specific.

## 7. Data required

- What data is used? Bar data, funding rate, open interest, basis, ...
- Is it available in QC Lean v17685 for BTCUSDT and ETHUSDT? Explicit
  yes/no.
- If no: this hypothesis is blocked until an alternative source is
  approved.

## 8. Execution model

- Order type.
- Entry bar / exit bar rule.
- No-leakage statement: signal bar vs execution bar.

## 9. Success / failure definition

- Success: criteria 1 to 6 all pass on OOS, then MC P5 > starting.
- Failure: any criterion fails.
- Trade-count expectation over window.

## 10. Risk controls

- Position sizing rule.
- Hard stop rule.
- Daily loss cap.

## 11. Links

- Candidate edge note: `obsidian/08_Data_Notes/CExxxx_<slug>.md`
- Strategy folder (after engineer): `strategies/Hxxxx_<slug>/`
- Backtest reports (after user run): `obsidian/04_Backtests/`
