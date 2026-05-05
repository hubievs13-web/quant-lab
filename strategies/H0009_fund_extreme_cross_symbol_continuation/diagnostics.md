# Diagnostics for H0009_fund_extreme_cross_symbol_continuation

Collect these outputs from QuantConnect after the smoke test and after any full backtest. Send the complete package to Devin/ChatGPT for the external verdict.

## Overview Metrics

Copy the QuantConnect Overview statistics:

- Trade count.
- OOS Sharpe.
- OOS net average trade.
- Max drawdown.
- Pre-fee average trade, computed from per-trade logs if QC does not show it directly.
- Win rate.
- Profit factor.
- Payoff ratio / profit-loss ratio.
- Net profit.
- Total orders.
- Total fees.
- Average win.
- Average loss.
- Expectancy.
- Start equity.
- End equity.

## Required Artifacts

- Equity curve CSV.
- Equity curve screenshot.
- Drawdown chart screenshot if available.
- Orders table export or screenshot.
- Per-trade log lines from Debug output.
- Per-symbol breakdown for BTCUSDT and ETHUSDT:
  - trade count;
  - average pre-fee PnL;
  - average post-fee PnL;
  - win rate;
  - profit factor;
  - max drawdown contribution if available.

## Debug Log Prefixes

Copy every Debug line beginning with:

- `INIT H0009`
- `CUSTOM_DATA_PATH_MISSING`
- `CUSTOM_DATA_INVALID`
- `SIGNAL`
- `SIGNAL_SKIPPED`
- `MAKER_ENTRY_EXPIRED`
- `ENTRY_ORDER_SUBMITTED`
- `ENTRY`
- `EXIT_ORDER_SUBMITTED`
- `ORDER_EVENT`
- `ORDER_EVENT_UNMATCHED`
- `TRADE`
- `TRADE_DETAIL`
- `DAILY_SUMMARY`
- `ORDER_SKIPPED_ZERO_QTY`
- `PROJECT_STOP`

## Per-Trade Log Requirements

Every closed trade must have a `TRADE_DETAIL` line containing:

- `timestamp`
- `symbol`
- `side`
- `signal_bar_time`
- `execution_bar_time`
- `delta_hours`
- `funding_time`
- `funding_rate`
- `funding_zscore`
- `entry_price`
- `exit_price`
- `holding_bars`
- `reason_code`
- `pre_fee_pnl_pct`
- `post_fee_pnl_pct`

Every `TRADE` line from `PerTradeLogger` must contain:

- `ts`
- `sym`
- `side`
- `entry`
- `exit`
- `bars`
- `reason`
- `pre_fee_pnl`
- `post_fee_pnl`

Check that every `execution_bar_time` is strictly later than `signal_bar_time`.

## Daily Summary Logs

Every `DAILY_SUMMARY` line must contain:

- `date`
- `trades`
- `win_rate`
- `avg_pre_fee`
- `avg_post_fee`
- `intraday_max_dd`

## Funding And Custom Data Checks

Report:

- Whether both custom funding URLs were configured.
- First and last timestamp in each funding CSV.
- Any `CUSTOM_DATA_PATH_MISSING` line.
- Any `CUSTOM_DATA_INVALID` line.
- Number of `SIGNAL` lines per symbol.
- Number of `SIGNAL_SKIPPED` lines per reason.
- Whether funding values are used only after their own timestamp.

## Brokerage And Symbol Checks

Copy any QuantConnect messages containing:

- Binance brokerage model unsupported warnings.
- BTCUSDT or ETHUSDT subscription errors.
- CryptoFuture or Market.BINANCE support warnings.
- Leverage warnings.
- Insufficient buying power.
- Invalid order quantity.
- Fee model errors.
- Log truncation warnings.

## Verdict Inputs

The Devin/ChatGPT verdict requires:

- Trade count >= 30 for B-Position swing branch.
- OOS Sharpe > 1.0.
- OOS net average trade > 0.
- Max drawdown < 25 percent.
- Tier M pre-fee average trade >= 0.20 percent.
- Win rate >= 50 percent in IS and OOS, OR profit factor >= 1.25 with stable payoff ratio.
- If criteria above pass: Monte Carlo with at least 1000 simulations and P5 final equity > $200.

Do not infer a PASS/FAIL verdict from screenshots alone. CSVs, orders, trades, and diagnostic logs are primary evidence.
