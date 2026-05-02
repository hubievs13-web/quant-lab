# Diagnostics for H0007_funding_settlement_unwind

Collect these outputs from QuantConnect after the smoke test and after any full backtest.

## Overview metrics

Copy the QuantConnect Overview statistics:

- Net Profit.
- Sharpe Ratio.
- Total Orders.
- Win Rate.
- Loss Rate.
- Profit-Loss Ratio or Profit Factor if shown.
- Drawdown.
- Average Win.
- Average Loss.
- Expectancy.
- Total Fees.
- Start Equity.
- End Equity.

## Charts and tables

- Equity curve screenshot.
- Drawdown chart screenshot if available.
- Orders list export or screenshot with timestamps, symbols, quantities, prices, and fees.
- Trades list export if available.

## Required Debug log prefixes

Copy all lines beginning with:

- `INIT H0007 params`
- `SIGNAL`
- `ENTRY_ORDER_SUBMITTED`
- `ENTRY`
- `EXIT_ORDER_SUBMITTED`
- `TRADE`
- `DAILY_SUMMARY`
- `DATA_GAP`
- `ORDER_SKIPPED_ZERO_QTY`
- `ORDER_ERROR`
- `ORDER_EVENT_UNMATCHED`
- `STATE_DESYNC`
- `STATE_DESYNC_FLATTEN`
- `SESSION_STOP`

## Per-trade log fields

Every `TRADE` line should contain:

- `timestamp`
- `symbol`
- `side`
- `signal_bar_time`
- `execution_bar_time`
- `delta_minutes`
- `entry_price`
- `exit_price`
- `holding_bars`
- `reason_code`
- `pre_fee_pnl_pct`
- `post_fee_pnl_pct`

Check that `delta_minutes` is strictly positive for every trade.

## Daily summary fields

Every `DAILY_SUMMARY` line should contain:

- `date`
- `trade_count`
- `win_rate_pct`
- `avg_pre_fee_edge_pct`
- `avg_post_fee_edge_pct`
- `max_intraday_drawdown_pct`

## Technical warnings to capture

Copy any QuantConnect messages containing:

- brokerage model unsupported warnings;
- symbol mapping or subscription errors for BTCUSDT or ETHUSDT;
- insufficient buying power;
- invalid order quantity;
- missing data;
- fee model or slippage model errors;
- log truncation warnings.

## Smoke-test acceptance evidence for ChatGPT review

For the 3-day smoke test, provide:

- date range used;
- whether BTCUSDT and ETHUSDT loaded;
- whether any `SIGNAL` lines appeared;
- whether any `ENTRY` and `TRADE` lines appeared;
- whether every `execution_bar_time` is later than `signal_bar_time`;
- whether any data, brokerage, buying power, or quantity warnings appeared.

Do not infer a final strategy verdict from the smoke test. The smoke test is only a technical validation step before a full backtest.
