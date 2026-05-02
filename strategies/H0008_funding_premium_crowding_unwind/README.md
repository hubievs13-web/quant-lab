# H0008_funding_premium_crowding_unwind

## Hypothesis

Implements `obsidian/02_Hypotheses/H0008_funding_premium_crowding_unwind.md`.

Persistent settled funding identifies a recently crowded leveraged side in Binance USD-M perpetuals. Premium-index compression against that crowded side is treated as confirmation that pressure may be unwinding. The mechanism is actual funding regime plus premium pressure, not scheduled funding-clock timing and not OHLCV-only price action.

## Free parameters

| Name | Value | Role | A priori justification |
|------|-------|------|------------------------|
| `funding_regime_abs_threshold` | 0.01 percent (`0.0001`) | Minimum absolute settled funding rate to define a crowded side. | Avoids treating near-zero funding as meaningful crowding. |
| `premium_compression_pct` | 0.015 percent (`0.00015`) | Minimum completed 5m premium-index compression against the crowded side. | Premium moves are smaller than last-price returns; this is intended to detect a real change in perp-reference pressure. |
| `hold_bars` | 3 | Fixed time exit after entry, measured in completed 5m bars. | Targets the first 15-minute repricing window without turning the idea into a broad trend/swing trade. |

No stop-loss, take-profit, trailing stop, cooldown, volatility filter, trend filter, daily loss cap, extra lookback, optimization hook, or additional threshold is added.

## Implementation constants

- Starting cash: 200 USDT.
- Account currency: USDT.
- Leverage: fixed 2x.
- Position sizing: fixed fractional equity, targeting 45 percent of equity margin per symbol at 2x notional exposure.
- One open position per symbol.
- Project hard stop: if drawdown from account peak reaches 20 percent, flatten positions and stop opening new trades.

These are implementation/risk controls, not hypothesis free parameters. Leverage is not an edge source.

## Fee and slippage assumptions

- Taker fee per side: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Slippage buffer per side: 0.05 percent.
- Round-trip slippage buffer: 0.10 percent.
- Total assumed round-trip friction: approximately 0.18 percent.
- Maker rebates are not assumed.
- Funding payments are not modeled separately in this implementation; if a position crosses a funding timestamp, that limitation must be reported to ChatGPT with the backtest evidence.

## Required custom data

H0008 requires audited local TIER 1 data that QuantConnect native data is not assumed to provide:

1. `funding_rate_history`
2. `premium_index_klines`

The strategy implements PythonData readers, but the exact custom-data hosting/upload path must be supplied in QuantConnect parameters before a valid smoke test:

| QC parameter | Expected content |
|---|---|
| `H0008_FUNDING_BTCUSDT_URL` | Remote CSV URL for BTCUSDT funding history. |
| `H0008_FUNDING_ETHUSDT_URL` | Remote CSV URL for ETHUSDT funding history. |
| `H0008_PREMIUM_BTCUSDT_URL` | Remote CSV URL for BTCUSDT premium-index 1m data. |
| `H0008_PREMIUM_ETHUSDT_URL` | Remote CSV URL for ETHUSDT premium-index 1m data. |

Expected funding schema:

```text
timestamp_utc,symbol,funding_rate,mark_price_at_funding,source,ingested_at_utc
```

Expected premium schema:

```text
timestamp_open_utc,timestamp_close_utc,symbol,open,high,low,close,source,ingested_at_utc
```

Files must be chronological CSV, not forward-filled, not backfilled, not interpolated, and not synthesized. Timestamp parsing accepts UTC ISO-8601 values with either `.000Z`-style fractional seconds or plain `Z` seconds, with no local timezone conversion. The DL0007 missing timestamps remain missing. If any custom-data URL parameter is missing, `main.py` logs `CUSTOM_DATA_PATH_MISSING` and disables trading. If any custom-data row cannot be parsed, `main.py` logs `CUSTOM_DATA_INVALID`, flattens open positions, and disables further trading.

## QC setup assumptions

- QuantConnect project: 30774195.
- Lean version: v17685.
- Futures subscription assumption: `add_crypto_future("BTCUSDT"/"ETHUSDT", Resolution.MINUTE, Market.BINANCE)`.
- Brokerage model assumption: `BrokerageName.BINANCE`, `AccountType.MARGIN`.
- Exact Binance USD-M perpetual symbol mapping and brokerage support must be verified in a smoke test. Do not silently assume support.

## Execution model

- BTCUSDT and ETHUSDT are evaluated independently.
- Minute futures bars are consolidated into completed 5m decision bars.
- Premium-index custom data is aggregated into completed 5m bars only when all 5 source minutes are present.
- DL0007 timestamps, `2024-08-12T10:02:00Z` and `2024-08-12T10:03:00Z`, are no-signal; any dependent 5m bar requiring complete price-state source data is no-signal.
- Funding values are usable only after their own timestamp.
- A signal from completed bar `t` can only submit an entry when algorithm time is strictly later than `signal_bar_time`.
- Exit is fixed after 3 completed 5m bars.

## Expected trade count

- Combined BTCUSDT and ETHUSDT: approximately 5 to 12 trades per day.
- Per symbol: approximately 2 to 6 trades per day.
- Per 12-month OOS window: roughly 1,800 to 4,300 combined candidate trades before no-signal exclusions.

These are hypothesis expectations, not results.

## Known risks and expected failure modes

- Funding can remain extreme during strong trends and make contrarian unwind entries lose repeatedly.
- Premium compression may occur only after last price has already repriced.
- Settled funding is discrete and may be stale relative to intraday positioning pressure.
- BTCUSDT and ETHUSDT may cluster during market-wide deleveraging.
- The raw unwind may fail to clear the 0.10 percent pre-fee floor or the 0.18 percent round-trip friction assumption.
- QC custom-data setup may fail or load too slowly unless files are compact and correctly hosted.

## Brokerage and custom-data verification steps

Before any full backtest:

1. Open QuantConnect project 30774195.
2. Paste `strategies/H0008_funding_premium_crowding_unwind/main.py` into `main.py`.
3. Configure the four required custom-data URL parameters.
4. Run a 3-day smoke test.
5. Confirm the log contains `INIT H0008 params` with `custom_data_ready=True`.
6. Confirm BTCUSDT and ETHUSDT subscriptions load without symbol mapping errors.
7. Confirm no brokerage-model unsupported warnings.
8. Confirm no `CUSTOM_DATA_PATH_MISSING` warning.
9. Confirm no `CUSTOM_DATA_INVALID` warning.
10. If any `SIGNAL`, `ENTRY`, or `TRADE` lines appear, confirm `execution_bar_time` is strictly later than `signal_bar_time`.
11. Confirm `DATA_GAP` lines appear only for known custom-data or DL0007 no-signal conditions, not broad missing files.

If custom data, brokerage, symbol mapping, or quantity support fails, do not proceed to a full backtest. Send the logs to ChatGPT for code review.

## Smoke-test instructions

Use a short 3-day range first. The smoke test is only a technical validation step and cannot produce a strategy verdict.

Collect:

- Overview metrics.
- Equity curve screenshot.
- Orders list.
- Debug logs with all required prefixes from `diagnostics.md`.
- Any custom-data warnings.
- Any brokerage or buying-power warnings.

## Files

- Strategy code: `strategies/H0008_funding_premium_crowding_unwind/main.py`
- Diagnostics plan: `strategies/H0008_funding_premium_crowding_unwind/diagnostics.md`
- Strategy note: `obsidian/03_Strategies/S0008_funding_premium_crowding_unwind.md`
