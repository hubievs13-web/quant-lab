# H0007_funding_settlement_unwind

## Hypothesis

Implements `obsidian/02_Hypotheses/H0007_funding_settlement_unwind.md`.

Binance USD-M perpetuals settle funding every 8 hours. The strategy fades a completed pre-settlement displacement only after the first post-settlement 5m bar is known. The mechanism is scheduled perpetual funding-settlement position management, not funding-rate prediction and not cross-asset lead-lag.

## Free parameters

| Name | Value | Role | A priori justification |
|------|-------|------|------------------------|
| `pre_settlement_window_minutes` | 30 | Measures displacement into funding settlement. | Captures short position-management flow before an 8-hour futures settlement event without becoming a broad trend regime. |
| `displacement_pct` | 0.35 percent | Minimum move from the start of the 30-minute window to the last completed close before settlement. | Large enough to be a meaningful BTCUSDT/ETHUSDT futures displacement rather than ordinary 5m noise. |
| `hold_bars` | 3 | Fixed exit after entry, measured in completed 5m bars. | Targets the immediate post-settlement unwind over about 15 minutes. |

No stop-loss, take-profit, trailing stop, cooldown, volatility filter, trend filter, funding-rate filter, OI filter, basis filter, or liquidation filter is added.

## Implementation constants

- Starting cash: 200 USDT.
- Account currency: USDT.
- Leverage: fixed 2x.
- Margin assumption: isolated margin in research notes; Lean implementation uses fixed fractional exposure and sets symbol leverage to 2x.
- Per-symbol margin fraction: 45 percent of equity, so two simultaneous positions target about 90 percent margin use at 2x.
- Session risk stop: if drawdown from the current UTC session equity peak reaches 20 percent, flatten positions and stop opening new trades until the next UTC day.

These are implementation/risk constraints, not hypothesis free parameters.

## Fee and slippage assumptions

- Taker fee model: 0.04 percent per side.
- Round-trip fee: 0.08 percent.
- Slippage model: 0.05 percent per side.
- Round-trip slippage buffer: 0.10 percent.
- Total assumed round-trip friction: about 0.18 percent.
- Maker rebates are not assumed.
- Historical funding-rate values are not used.

## Execution model

- Data: minute Binance USD-M futures bars consolidated into 5m bars.
- Funding settlement schedule: 00:00, 08:00, and 16:00 UTC.
- Signal per symbol is independent.
- The pre-settlement displacement uses the close at settlement minus 30 minutes and the last completed 5m close before settlement.
- The first post-settlement 5m bar must complete before a signal can be created.
- Entry is submitted only when algorithm time is strictly greater than the signal bar timestamp.
- Exit is a fixed time exit after 3 completed 5m bars from entry.
- New same-symbol signals are ignored while a position is open.

## Expected trade count

- Expected combined BTCUSDT and ETHUSDT trade frequency from hypothesis: 4 to 10 trades per day.
- Expected 12-month OOS count from hypothesis: roughly 1,400 to 3,600 completed trades before missing-data and overlap exclusions.

These are expectations from the hypothesis, not backtest results.

## QuantConnect verification step

Before trusting any full backtest:

1. Open QuantConnect project `30774195`.
2. Paste `strategies/H0007_funding_settlement_unwind/main.py` into `main.py`.
3. Run a 3-day smoke test that includes at least one 00:00, 08:00, and 16:00 UTC funding settlement.
4. Confirm the log contains `INIT H0007 params`.
5. Confirm BTCUSDT and ETHUSDT subscriptions load without symbol mapping errors.
6. Confirm there are no warnings that the Binance brokerage model does not support the securities.
7. Confirm any `SIGNAL`, `ENTRY`, and `TRADE` logs have `execution_bar_time` strictly later than `signal_bar_time`.
8. Confirm fills, if any, use nonzero quantities and no recurring insufficient buying power errors.

If symbol mapping or brokerage support fails under Lean v17685, do not run the full backtest. Treat the package as technically blocked until the mapping is corrected and reviewed.

## Diagnostics to extract

See `diagnostics.md`. The key evidence is QuantConnect overview metrics, orders, equity curve, and Debug logs containing `SIGNAL`, `ENTRY_ORDER_SUBMITTED`, `ENTRY`, `EXIT_ORDER_SUBMITTED`, `TRADE`, `DAILY_SUMMARY`, `DATA_GAP`, `ORDER_SKIPPED_ZERO_QTY`, `ORDER_ERROR`, `ORDER_EVENT_UNMATCHED`, `STATE_DESYNC`, `STATE_DESYNC_FLATTEN`, and `SESSION_STOP`.

## Known risks and expected failure modes

- Pre-settlement displacement may be information-driven and continue after settlement.
- Actual funding-rate magnitude may be necessary, but H0007 does not use funding-rate history because QC-native availability is not confirmed.
- Reversal may happen inside the first post-settlement bar before delayed execution.
- BTCUSDT and ETHUSDT signals may cluster around the same macro event.
- Average raw reversal may be below the 0.18 percent round-trip friction assumption.
- QC Binance Futures symbol support or lot sizing may create invalid orders with 200 USDT starting capital.

## Files

- Strategy code: `strategies/H0007_funding_settlement_unwind/main.py`
- Diagnostics plan: `strategies/H0007_funding_settlement_unwind/diagnostics.md`
- Strategy note: `obsidian/03_Strategies/S0007_funding_settlement_unwind.md`
