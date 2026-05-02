---
id: S0008
hypothesis: H0008
slug: funding_premium_crowding_unwind
created: 2026-05-02
status: draft
---

# S0008 - funding_premium_crowding_unwind (implements H0008)

## 1. Link to hypothesis

`obsidian/02_Hypotheses/H0008_funding_premium_crowding_unwind.md`

## 2. Mechanism summary

Persistent settled funding identifies a recently crowded leveraged side in Binance USD-M perpetuals. Premium-index compression against that crowded side is treated as confirmation that pressure may be unwinding. This is actual funding regime plus premium pressure, not scheduled funding-clock timing and not OHLCV-only price action.

## 3. Free parameters (<= 3)

| Name | Value | Role | Justification |
|------|-------|------|---------------|
| `funding_regime_abs_threshold` | 0.01 percent | Minimum absolute settled funding rate to define crowded funding regime. | Avoids treating near-zero funding as meaningful crowding. |
| `premium_compression_pct` | 0.015 percent | Minimum completed 5m premium-index compression against crowded side. | Detects a meaningful change in perp-reference pressure without adding OHLCV-only filters. |
| `hold_bars` | 3 | Fixed time exit after entry. | Targets the first 15-minute repricing window. |

## 4. Fee and slippage assumptions

- Taker fee per side: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Slippage per side: 0.05 percent.
- Round-trip slippage buffer: 0.10 percent.
- Total round-trip friction assumption: approximately 0.18 percent.
- Funding payments: not separately modeled; if a position crosses a funding timestamp, that limitation must be reported with the backtest evidence.

No deviation from `obsidian/01_Rules/02_Fee_Slippage_Model.md`.

## 5. Execution model

- Minute futures bars are consolidated into completed 5m decision bars.
- Custom funding data is used only after its funding timestamp.
- Custom premium-index data is aggregated into completed 5m bars only when all 5 source minutes are available.
- Custom data timestamps are parsed as UTC ISO-8601 with either fractional seconds plus `Z` or plain seconds plus `Z`; invalid custom-data rows trigger `CUSTOM_DATA_INVALID`, flatten open positions, and disable further trading.
- DL0007 missing timestamps and dependent incomplete 5m price-state bars are no-signal.
- Entry is submitted only when algorithm time is strictly later than the signal bar timestamp.
- BTCUSDT and ETHUSDT are evaluated independently; no cross-asset signal is used.

## 6. Expected trade count

- Combined BTCUSDT and ETHUSDT: approximately 5 to 12 trades per day.
- Per symbol: approximately 2 to 6 trades per day.
- Per 12-month OOS window: roughly 1,800 to 4,300 combined candidate trades before no-signal exclusions.

These are expectations from the hypothesis, not backtest results.

## 7. Diagnostics plan

See `strategies/H0008_funding_premium_crowding_unwind/diagnostics.md`.

## 8. Known risks and expected failure modes

- Funding can stay extreme during a strong trend.
- Premium compression may happen after last price has already repriced.
- Settled funding may be stale for intraday positioning pressure.
- BTCUSDT and ETHUSDT signals can cluster during broad market deleveraging.
- Raw edge may not clear the 0.10 percent pre-fee floor or 0.18 percent round-trip friction.
- QC custom-data setup may fail or be too slow if files are not hosted in the expected schema.

## 9. Brokerage and custom-data verification step

QuantConnect Lean v17685 exposes Binance-related brokerage models and crypto futures subscriptions, but exact USD-M perpetual symbol mapping may vary. H0008 also requires custom funding and premium-index CSV streams. Before the first full backtest, the user must:

1. Open QuantConnect project 30774195.
2. Paste `strategies/H0008_funding_premium_crowding_unwind/main.py`.
3. Configure `H0008_FUNDING_BTCUSDT_URL`, `H0008_FUNDING_ETHUSDT_URL`, `H0008_PREMIUM_BTCUSDT_URL`, and `H0008_PREMIUM_ETHUSDT_URL`.
4. Run a 3-day smoke test.
5. Confirm:
   - BTCUSDT and ETHUSDT subscriptions load.
   - `custom_data_ready=True`.
   - There are no brokerage-model unsupported warnings.
   - There is no `CUSTOM_DATA_INVALID` warning.
   - `execution_bar_time` is strictly later than `signal_bar_time` in every `ENTRY` and `TRADE` line.
   - No broad custom-data gaps appear beyond known no-signal conditions.
6. If any of the above fails, do not proceed to the full backtest. Record the observed behavior and send it for code review.

## 10. Paste-ready code

See `strategies/H0008_funding_premium_crowding_unwind/main.py`.
