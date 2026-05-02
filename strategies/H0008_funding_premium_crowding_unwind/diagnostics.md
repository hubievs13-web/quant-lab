# Diagnostics for H0008_funding_premium_crowding_unwind

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
- Average Trade if shown.
- Start Equity.
- End Equity.

## Equity curve screenshot

Capture:

- Full equity curve screenshot.
- Drawdown chart screenshot if available.

## Orders list

Export or screenshot the orders table with:

- order timestamp;
- symbol;
- quantity;
- direction;
- fill price;
- fees;
- order status;
- order tag.

## Debug logs

Copy all lines beginning with:

- `INIT H0008 params`
- `CUSTOM_DATA_PATH_MISSING`
- `CUSTOM_DATA_INVALID`
- `SYMBOL_MAPPING`
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
- `PROJECT_STOP`

## Per-trade logs

Every `TRADE` line must contain:

- `timestamp`
- `symbol`
- `side`
- `signal_bar_time`
- `execution_bar_time`
- `delta_minutes`
- `funding_regime_value`
- `premium_compression_value`
- `entry_price`
- `exit_price`
- `holding_bars`
- `reason_code`
- `pre_fee_pnl_pct`
- `post_fee_pnl_pct`

Check that `delta_minutes` is strictly positive for every trade.

## Daily summary logs

Every `DAILY_SUMMARY` line must contain:

- `date`
- `trade_count`
- `win_rate_pct`
- `avg_pre_fee_edge_pct`
- `avg_post_fee_edge_pct`
- `max_intraday_drawdown_pct`
- `no_signal_count`
- `data_gap_flags`
- `custom_data_ready`
- `custom_data_missing_count`

## Data gap and custom data warnings

Copy any lines containing:

- `CUSTOM_DATA_PATH_MISSING`
- `CUSTOM_DATA_INVALID`
- `DATA_GAP`
- `custom_data_ready=False`
- `custom_data_missing_count`
- missing funding data;
- missing premium-index data;
- DL0007 no-signal flags.

## Brokerage model warnings

Copy any QuantConnect messages containing:

- brokerage model unsupported warnings;
- symbol mapping or subscription errors for BTCUSDT or ETHUSDT;
- CryptoFuture / Binance support warnings;
- leverage warnings;
- insufficient buying power;
- invalid order quantity;
- fee model errors;
- slippage model errors;
- log truncation warnings.

## Smoke-test package for ChatGPT

Send ChatGPT:

- date range used;
- whether BTCUSDT and ETHUSDT loaded;
- whether custom data loaded with `custom_data_ready=True`;
- whether any `SIGNAL` lines appeared;
- whether any `ENTRY` and `TRADE` lines appeared;
- whether every `execution_bar_time` is later than `signal_bar_time`;
- whether any data, brokerage, buying power, or quantity warnings appeared;
- overview metrics and equity curve screenshot;
- relevant Debug log excerpt.

Do not infer a strategy verdict from the smoke test. The smoke test is only a technical validation step.
