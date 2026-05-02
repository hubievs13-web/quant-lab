# Smoke Test Checklist - H0005_perp_compression_breakout

Run window:

- Start: 2024-01-01
- End: 2024-01-08

## Compile and data

- [ ] Code compiles in QuantConnect.
- [ ] Crypto futures symbols subscribe successfully.
- [ ] `SYMBOL_MAPPING` logs show actual BTC and ETH Symbol objects.
- [ ] 5m bars arrive for BTC.
- [ ] 5m bars arrive for ETH.
- [ ] No spot, CFD, or proxy data is used.

## Signal path

- [ ] Compression windows are checked.
- [ ] At least one compression is detected, or logs explain none via low `compression_detected_count`.
- [ ] At least one breakout signal is detected, or logs explain none via zero breakout counts.
- [ ] Entry order is submitted if a breakout signal occurs.
- [ ] Entry fill or inferred entry is detected.
- [ ] Exit happens after 3 completed 5m bars.

## Safety diagnostics

- [ ] No same-bar execution violation.
- [ ] No `MARGIN_CALL` or `MARGIN_CALL_WARNING`.
- [ ] No `MarginCallOrder`.
- [ ] No `STATE_ERROR`.
- [ ] No log limit exceeded.
- [ ] No stuck open position at end unless final bars prevented exit.
- [ ] No excessive buying power errors.
- [ ] Final summary printed.

## Required logs to copy

- [ ] `INIT H0005_perp_compression_breakout`.
- [ ] `SYMBOL_MAPPING`.
- [ ] `SIGNAL`, if any.
- [ ] `ENTRY_SUBMITTED`, if any.
- [ ] `ENTRY_FILLED` or `ENTRY_FILLED_INFERRED`, if any entry is submitted.
- [ ] `EXIT_SUBMITTED`, if any entry is filled.
- [ ] `TRADE_EXIT` or `TRADE_EXIT_INFERRED`, if any exit occurs.
- [ ] `FINAL_SYMBOL_SUMMARY` for BTC and ETH.
- [ ] `FINAL_PORTFOLIO_SUMMARY`.

## Fail smoke test if

- [ ] Code does not compile.
- [ ] Futures symbols do not map to Binance Crypto Futures / USD-M compatible data.
- [ ] 5m bars do not arrive.
- [ ] Same-bar execution violation appears.
- [ ] Margin call appears.
- [ ] Entry is submitted but no fill/inferred fill and no clear order error appears.
- [ ] Exit is not submitted after 3 completed 5m bars.
- [ ] A position remains stuck open beyond expected exit.
- [ ] Logs exceed the QuantConnect limit.
