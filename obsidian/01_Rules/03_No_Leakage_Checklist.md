# 03_No_Leakage_Checklist

Every strategy must pass all items.

## Time

- No access to bars with timestamp >= current bar's execution time.
- No use of the current bar's close for a signal that executes at the
  current bar's close. Execute at next bar open or with market-on-open /
  market-on-next-bar orders.
- Indicator warm-up consumes past bars only. Warm-up data is part of
  in-sample history; if it leaks OOS data, it is a leakage bug.

## Multi-asset

- When BTCUSDT's signal is used to trade ETHUSDT (or vice versa), the
  execution bar on the target symbol must be strictly after the signal
  bar on the source symbol. Align by wall-clock timestamp available at
  execution time.
- Do not compare bars by index when symbols may have different
  listing timezones or missing bars.

## Data

- No OOS data in IS. OOS window must be completely unseen during
  hypothesis formation and any code tweak.
- No look-ahead from rolling windows (end-of-window value that depends
  on future bars in that window).
- No forward-fill of derived signals with future values.

## Labels

- If you train or calibrate anything, the label window must not overlap
  the feature window.

## Diagnostic

Every strategy must log, per trade:

- signal bar timestamp,
- execution bar timestamp,
- delta between them (must be > 0).
