# Diagnostics - H0002_btc_perp_eth_lag

## 1. Pre-backtest checklist

- Confirm the copied file is exactly `strategies/H0002_btc_perp_eth_lag/main.py`.
- Confirm the only hypothesis parameters in code are:
  - `BTC_IMPULSE_PCT = 0.35`
  - `ETH_MAX_SAMEBAR_MOVE_PCT = 0.12`
  - `HOLD_BARS = 3`
- Confirm there is no stop-loss, take-profit, volatility filter, time-of-day filter, volume filter, cooldown, funding filter, OI filter, liquidation input, optimizer, ML, external data, or web request.
- Confirm brokerage and data are Binance USD-M Futures for BTCUSDT and ETHUSDT. If QC shows spot, CFD, or another proxy, stop and mark BLOCKED.
- Run the first smoke test on a 3-7 day window only, not on a full-year window.
- Confirm the smoke-test logs contain `INIT H0002 btc_perp_eth_lag`.
- Confirm no QC warning says the brokerage model, security type, or symbol mapping is unsupported.
- Confirm USD 200 starting cash and 2x leverage are reflected in the run setup or logs.

## 2. What to inspect in logs

Required line types:

- `INIT H0002 btc_perp_eth_lag`
- `SIGNAL`
- `ENTRY_SUBMITTED`
- `ORDER_EVENT`
- `ENTRY_FILLED`
- `ENTRY_FILLED_INFERRED`
- `EXIT_SUBMITTED`
- `TRADE_EXIT`
- `TRADE_EXIT_INFERRED`
- `DAILY_SUMMARY`
- `BLOCKED zero_quantity` if position sizing cannot produce a valid ETHUSDT order.

For every trade, inspect:

- `btc_signal_ts`
- `eth_comparison_ts`
- `planned_eth_execution_ts`
- `entry_fill_algorithm_time`
- `btc_impulse_pct`
- `eth_samebar_move_pct`
- `direction`
- `entry_price`
- `exit_price`
- `holding_bars`
- `exit_reason`
- `pre_fee_pnl_pct`
- `post_fee_estimate_pct`
- `full_friction_reference_pct`

Expected timing:

- `btc_signal_ts` must equal `eth_comparison_ts`.
- `planned_eth_execution_ts` must be strictly greater than `btc_signal_ts`.
- `entry_fill_algorithm_time` is QuantConnect algorithm time for fill diagnostics and may use a different display timezone; do not use it for the no-leakage timestamp comparison.
- `holding_bars` must be 3 on `TRADE_EXIT` or `TRADE_EXIT_INFERRED`.
- `exit_reason` must be `time_exit`.

## 3. Leakage bug signs

- `planned_eth_execution_ts` is equal to or earlier than `btc_signal_ts`.
- A trade enters on the same completed 5m close that created the signal.
- `btc_signal_ts` and `eth_comparison_ts` do not match for a generated signal.
- Entry occurs before both BTCUSDT and ETHUSDT comparison bars are complete.
- Logs show future ETH/BTC bars used before the execution timestamp.
- Holding bars are not exactly 3 at exit.
- Holding period exceeds 3 completed ETHUSDT 5m bars.

## 4. Data or symbol mapping problem signs

- QC compile error for `BrokerageName.BINANCE`.
- QC compile error for `add_crypto_future`.
- QC warning says Binance brokerage does not support the requested symbol.
- BTCUSDT or ETHUSDT resolves as spot, CFD, or another non-futures security.
- No 5m consolidated bars appear after the smoke test begins.
- No `SIGNAL` lines appear in a multi-day active market window, and logs also show missing bars or data gaps.
- `BLOCKED zero_quantity` appears repeatedly because lot size prevents USD 200 / 2x orders.
- Fees are zero or clearly inconsistent with 0.04 percent taker per side.
- Slippage/fill prices appear inconsistent with the configured 0.05 percent per side buffer.
- Any `MarginCallOrder` appears in orders or logs.
- `ENTRY_SUBMITTED` appears without a later `ENTRY_FILLED` or `ENTRY_FILLED_INFERRED`, followed by `TRADE_EXIT` or `TRADE_EXIT_INFERRED`.
- The position remains invested after `holding_bars` exceeds 3 completed ETHUSDT 5m bars.
- Repeated `STATE_WARNING` spam appears; each warning type should be logged at most once per trade.
- `ENTRY_FILLED_INFERRED` is acceptable for the smoke test if it is followed by `EXIT_SUBMITTED` and `TRADE_EXIT` or `TRADE_EXIT_INFERRED`.
- Logs exceed the QuantConnect 100kb limit.

## 5. QuantConnect artifacts to save after the run

Create a folder after the backtest:

`results/raw/BTxxxx_H0002_YYYY-MM-DD/`

Save these files there when available:

- `overview.png`
- `equity_curve.png`
- `trades.csv`
- `orders.csv`
- `logs.txt`
- `statistics.txt` or `statistics.json`
- `runtime_errors.txt` if QC reports runtime or brokerage warnings

Do not write to `obsidian/04_Backtests/` manually before processing artifacts.

## 6. Post-run processing command

After saving the raw QuantConnect artifacts, run from the repository root:

```powershell
python scripts/process_qc_backtest.py --hypothesis H0002 --strategy S0001 --raw-dir results/raw/BTxxxx_H0002_YYYY-MM-DD
```

Replace `BTxxxx` and `YYYY-MM-DD` with the actual backtest ID and run date used for the raw artifact folder.

The script output is evidence for Devin review only. Do not treat it as a final verdict.
