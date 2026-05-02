# H0005_perp_compression_breakout

## 1. Hypothesis summary

H0005 tests a same-symbol Binance USD-M perpetual compression breakout on BTCUSDT and ETHUSDT. After a tight 12-bar 5m futures range, a completed 5m close above the range high enters long on the next available bar; a completed close below the range low enters short. Exit is fixed after 3 completed 5m bars.

Hypothesis note: `obsidian/02_Hypotheses/H0005_perp_compression_breakout.md`

## 2. Fixed parameters

| Name | Value | Role |
|------|-------|------|
| compression_bars | 12 | Previous completed 5m bars used for compression range. |
| max_compression_range_pct | 0.35 percent | Maximum prior range width. |
| hold_bars | 3 | Fixed exit after completed 5m bars. |

These are fixed hypothesis parameters. Do not optimize them.

## 3. What the strategy does

- Subscribes to BTCUSDT and ETHUSDT Crypto Futures on Binance in QuantConnect.
- Consolidates minute data to 5m bars.
- For each symbol independently, evaluates the previous 12 completed 5m bars.
- If the prior range is compressed and the current completed 5m close breaks out, submits a same-symbol market entry on the next available bar.
- Holds for 3 completed 5m bars and exits by time.
- BTC and ETH can both have positions at the same time.

## 4. What it intentionally does not do

- No H0002 BTC-to-ETH lead-lag logic.
- No cross-asset signals.
- No funding, open interest, basis, liquidation, spot, CFD, external API, or custom data.
- No stop-loss, take-profit, trailing stop, cooldown, time filter, trend filter, volatility filter, spread filter, optimizer, or adaptive thresholds.

## 5. No-leakage implementation notes

- Compression window excludes the current breakout bar.
- Signal is generated only after the breakout 5m bar is complete.
- Entry is submitted only on a later available bar, where `planned_execution_time > signal_time`.
- The code logs `LEAKAGE_VIOLATION same_bar_execution` if this relationship fails.
- Each trade log includes `signal_time`, `planned_execution_time`, entry fill time when available, holding bars, and exit reason.

## 6. Fee, slippage, and sizing assumptions

- Research fee assumption: Binance Futures taker fee 0.04 percent per side.
- Code applies a custom 0.04 percent taker fee model per side.
- Code applies 0.05 percent slippage per side, so fee plus slippage reference is approximately 0.18 percent round trip.
- Sizing is fixed implementation logic: up to 40 percent of portfolio equity per symbol at 2x notional exposure.
- This sizing is intended to reduce Insufficient Buying Power errors on 200 USDT starting capital; it is not a hypothesis parameter.
- Isolated margin is the intended real-exchange assumption. QC margin modeling must be verified.

## 7. QC symbol mapping risk

The code uses:

```python
add_crypto_future("BTCUSDT", Resolution.MINUTE, market=Market.BINANCE)
add_crypto_future("ETHUSDT", Resolution.MINUTE, market=Market.BINANCE)
```

QuantConnect symbol mapping may differ by Lean version or dataset. The smoke test must confirm that the created `Symbol` objects are Binance Crypto Futures / USD-M compatible and not spot, CFD, or proxy data. If BTCUSDT or ETHUSDT futures bars are unavailable, mark H0005 BLOCKED and do not substitute another ticker.

## 8. Smoke test instructions

Run only:

- Start: 2024-01-01
- End: 2024-01-08

Check:

- Code compiles.
- `INIT H0005_perp_compression_breakout` appears.
- `SYMBOL_MAPPING` logs show BTCUSDT and ETHUSDT subscriptions.
- `FINAL_SYMBOL_SUMMARY` appears for both symbols.
- 5m bars arrive (`bars_seen > 0`).
- Compression windows are checked.
- If signals occur, entries and exits complete.
- No `LEAKAGE_VIOLATION`.
- No `MARGIN_CALL` or `MARGIN_CALL_WARNING`.
- No repeated order errors or excessive buying power errors.

## 9. Full backtest instructions

Only after smoke test passes, run manually:

- Start: 2024-01-01
- End: 2025-01-01

Save overview, equity curve, orders, trades, logs, and statistics for review. Do not tune H0005 after results.

## 10. Falsification criteria reminder

H0005 must satisfy all required criteria before Monte Carlo is allowed:

- >= 300 completed OOS trades for intraday.
- OOS Sharpe > 1.0.
- OOS net average trade > 0.
- Max drawdown < 25 percent.
- Pre-fee average trade >= 0.10 percent.
- Win rate >= 50 percent in IS/OOS or profit factor >= 1.25 with stable payoff.
- Monte Carlo only after criteria 1-6 pass.

No result should be called passing before Devin review and Monte Carlo.
