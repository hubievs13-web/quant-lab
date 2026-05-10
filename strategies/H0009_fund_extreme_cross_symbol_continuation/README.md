# H0009_fund_extreme_cross_symbol_continuation

## Hypothesis

Implements `obsidian/02_Hypotheses/H0009_fund_extreme_cross_symbol_continuation.md`.

After a `FUND_EXTREME` event, extreme positive OR negative funding can mark forced positioning pressure that clears the order book. In the cited 3-year sample, forced liquidations cleared the order book and the asset reverted toward the prevailing multi-month trend. The strategy is always long after a `FUND_EXTREME` firing on BTCUSDT or ETHUSDT and holds over the h+72 horizon.

## Profile

- Profile: B-Position.
- Execution tier: Tier M, maker-mostly.
- Universe: BTCUSDT and ETHUSDT Binance USD-M Futures.
- Resolution: 1h.
- Direction: always long after any `FUND_EXTREME` firing, regardless of funding sign.
- Event horizon: h+72.
- Expected frequency: approximately 2 combined trades per week from BTC n=156 plus ETH n=136 over roughly 3 years.
- Expected pre-fee edge: BTCUSDT +1.10 percent; ETHUSDT +0.98 percent.

Funding-sign split in the cited 3-year sample:

| Symbol | Positive funding | Negative funding | All FUND_EXTREME |
|---|---:|---:|---:|
| BTCUSDT | n=84, mean +1.61% | n=72, mean +0.50% | n=156, mean +1.10% |
| ETHUSDT | n=77, mean +1.11% | n=59, mean +0.82% | n=136, mean +0.98% |

Both funding-sign branches went up. The strategy therefore does not trade in the sign of funding; it always uses side `+1`.

Quoted Data Layer evidence:

```text
| M | long | 1h | FUND_EXTREME | h+72 | 156 | +1.00% | 0.021 | 136 | +0.88% | 0.066 |
```

## Free Parameters

| Name | Value | Role | A priori justification |
|------|-------|------|------------------------|
| `FUNDING_EXTREME_ZSCORE` | `2.0` | Fires `FUND_EXTREME` when 30-day funding z-score is at least 2 in absolute value. | Matches event catalog rule: `EV_FUND_EXTREME`: `|funding_rate_zscore_30d| >= 2`; funding is observed every 8 hours, so the code requires 90 observations before z-score evaluation. |
| `HOLD_HOURS` | `72` | Fixed time exit after entry. | Matches the cited `h+72` Data Layer horizon. |
| `PER_TRADE_STOP_FRAC` | `0.01` | Hard per-trade drawdown stop at -1 percent from entry. | Risk constraint requested for this implementation; not optimized from results. |

No stop-profit, trailing stop, cooldown, volatility filter, alternate funding threshold, or symbol selector is added.

## Fee And Slippage Assumptions

- Tier M maker fee: 0.02 percent per side.
- No maker rebate is assumed.
- Maker adverse-selection proxy: a limit fill is accepted only when the next bar touches the limit and closes at least 0.05 percent adverse to the fill side.
- Pure maker round-trip friction assumption: approximately 0.08 percent.
- Pre-fee floor for Tier M: 0.20 percent.
- Unfilled maker entry signals are canceled; there is no taker fallback for entries.
- Time-stop and hard-stop exits are submitted immediately for risk control; if QC treats these as taker-like executions, report that as a known friction risk to Devin/ChatGPT.

## Fee Budget Gate

```text
notional_per_trade  = starting_capital * margin_fraction * leverage
                    = 200 * 0.5 * 2 = 200
trades_per_year     = trades_per_week * 52
                    = 2 * 52 = 104
annual_friction     = trades_per_year * notional_per_trade * round_trip_friction
                    = 104 * 200 * 0.0008 = 16.64
ratio               = annual_friction / starting_capital
                    = 16.64 / 200 = 0.0832 = 8.32%
```

The 8.32 percent ratio is below the 25 percent maximum.

## Required Custom Data

QC native funding-rate availability for BTCUSDT and ETHUSDT USD-M Futures under Lean v17685 has NOT been verified. This implementation therefore uses explicit custom funding CSV parameters and disables trading when the parameters are absent.

Required QuantConnect parameters:

| QC parameter | Expected content |
|---|---|
| `H0009_FUNDING_BTCUSDT_URL` | Remote CSV URL for BTCUSDT funding history. |
| `H0009_FUNDING_ETHUSDT_URL` | Remote CSV URL for ETHUSDT funding history. |

Expected minimum CSV schema:

```text
timestamp_utc,symbol,funding_rate,...
```

Rows must be chronological UTC timestamps. Funding values are used only after their own timestamp.
During `initialize`, the strategy also calls `Download(...)` on each CSV URL and backfills
pre-start funding rows (`timestamp_utc < start_date`) into the per-symbol funding history;
the `add_data` stream then continues from `start_date` onward.

## Execution Model

- Add BTCUSDT and ETHUSDT with `add_crypto_future(..., Resolution.HOUR, market=Market.BINANCE)`.
- Maintain a rolling funding history per symbol.
- Fire `FUND_EXTREME` when `|funding_rate_zscore_30d| >= 2`; since funding is observed every 8 hours, the z-score branch requires at least 90 observations.
- The 5 bp absolute-rate fallback was removed; signals are z-score only, and warmup now seeds pre-start funding history to close the initialization gap.
- Positive funding extreme trades long; negative funding extreme also trades long. The side field remains in logs and data structures, but is hard-coded to `+1` for this hypothesis.
- Submit a maker-entry proxy limit at the latest completed 1h close.
- On the next 1h bar, enter only if the bar touched the limit and closed at least 0.05 percent adverse to the fill side.
- Cancel unfilled or non-adverse maker entries; no taker fallback.
- Per-symbol notional is sized at 48 percent of total portfolio value so two simultaneous positions at 2x leverage target ~96 percent aggregate margin usage and leave headroom for fees/rounding.
- Exit at h+72 hours, or earlier if the per-trade drawdown reaches -1 percent.
- Project-level hard stop: if drawdown from session/account peak reaches 20 percent, flatten and stop.

## Expected Trade Count

- Expected combined frequency: approximately 2 trades per week.
- Expected 3-year candidate event count: 292 combined events before fill cancellations, overlap exclusions, and stop-outs.
- Swing falsification threshold: at least 30 completed OOS trades.

## Expected Failure Modes

1. The recovery/uptrend regime ends and the always-long post-FUND_EXTREME effect does not survive in an extended bear regime.
2. Funding payments during a 72-hour hold reduce or erase the price edge, especially when the position pays funding.
3. Maker adverse-selection fills admit a worse subset than the event-level Data Layer summary.
4. BTCUSDT and ETHUSDT events cluster during the same macro regimes, increasing drawdown.
5. Custom funding data alignment or QC custom-data hosting fails, disabling valid signal generation.
6. Hard-stop exits may incur taker-like friction not captured by the Tier M edge summary.

## Regime Caveat

This signal was validated on a recovery / uptrend regime in the 2023-2026 sample, dominated by BTC/ETH recovery and continuation behavior. If the prevailing trend reverses into an extended bear regime, the always-long direction must be re-validated before relying on it. After deployment or paper trading, monitor monthly post-event outcomes by symbol and by funding sign to detect decay or sign reversal.

## Known Risks

- QuantConnect native Binance USD-M funding history has not been verified.
- Exact Binance USD-M perpetual symbol mapping under Lean v17685 may differ from `add_crypto_future("BTCUSDT", ...)`.
- The implementation uses custom funding data; missing URLs produce `CUSTOM_DATA_PATH_MISSING` and no trading.
- The event catalog is reproduced from summary rules, not imported from `data_layer` at runtime.
- Funding payments themselves are not debited separately in the strategy PnL; the user must report funding-related limitations in review.

## Brokerage And Data Verification Step

Before relying on any backtest:

1. Open QuantConnect project 30774195.
2. Paste `strategies/H0009_fund_extreme_cross_symbol_continuation/main.py`.
3. Set `H0009_FUNDING_BTCUSDT_URL` and `H0009_FUNDING_ETHUSDT_URL` to hosted chronological CSVs.
4. Run a 3-7 day smoke test.
5. Confirm BTCUSDT and ETHUSDT subscriptions load under `BrokerageName.BINANCE_FUTURES` with no brokerage/model mismatch warnings (cash-as-margin for USD-M futures requires the futures brokerage model, not spot Binance).
6. Confirm no `CUSTOM_DATA_PATH_MISSING` or `CUSTOM_DATA_INVALID` lines appear.
7. Confirm any `ENTRY` line has `execution_bar_time` strictly later than `signal_bar_time`.
8. If any data, symbol, brokerage, leverage, or custom-data warning appears, stop and send logs for review before a full backtest.

## Lint

```text
python scripts/lint_strategy.py strategies/H0009_fund_extreme_cross_symbol_continuation/main.py
path: strategies\H0009_fund_extreme_cross_symbol_continuation\main.py
profile: B-Position
tier: M
findings: none
LINT: PASS
```

## Files

- Strategy code: `strategies/H0009_fund_extreme_cross_symbol_continuation/main.py`
- Diagnostics plan: `strategies/H0009_fund_extreme_cross_symbol_continuation/diagnostics.md`
