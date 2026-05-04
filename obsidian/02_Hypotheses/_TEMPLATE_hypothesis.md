---
id: Hxxxx
slug: short_slug
status: draft   # draft | active | rejected | preliminary_pass | final_pass
created: YYYY-MM-DD
mechanism_class: funding | oi | basis | lead_lag | orderflow | other
symbols: [BTCUSDT, ETHUSDT]
timeframe: 1m | 5m
profile: A-Maker | A-Taker | B   # one of `.codex/AGENTS.md` Section 3 profiles
execution_tier: M | T            # M for maker (limit + adverse-selection), T for taker (market)
expected_trades_per_day: [low, high]
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

## 3b. Fee budget gate

Show the arithmetic from
`obsidian/01_Rules/02_Fee_Slippage_Model.md`:

```
notional_per_trade = starting_capital * margin_fraction * leverage
annual_friction    = trades_per_day * 365
                     * notional_per_trade * round_trip_friction
ratio              = annual_friction / starting_capital
```

Profile values used:
- starting_capital: ...
- margin_fraction: ...
- leverage: ...
- trades_per_day: ...
- round_trip_friction: 0.0018 (Tier T) or 0.0008 (Tier M)

Result ratio: ... (must be <= 0.25 to pass).

## 4. Expected trade frequency

- Per day per symbol: ...
- Per backtest window (12 months OOS): ...
- Must plausibly reach >= 300 trades over the OOS window to satisfy
  criterion 1 of the framework.

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
