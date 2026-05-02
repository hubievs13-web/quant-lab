---
id: S0007
hypothesis: H0007
slug: funding_settlement_unwind
created: 2026-05-01
status: draft
---

# S0007 - funding_settlement_unwind (implements H0007)

## 1. Link to hypothesis

`obsidian/02_Hypotheses/H0007_funding_settlement_unwind.md`

## 2. Mechanism summary

Binance USD-M perpetual futures settle funding every 8 hours. The strategy fades a completed pre-settlement displacement only after the first post-settlement 5m bar is known. The mechanism is scheduled perpetual funding-settlement position management, not funding-rate prediction, open-interest filtering, or cross-asset lead-lag.

## 3. Free parameters (<= 3)

| Name | Value | Role | Justification |
|------|-------|------|---------------|
| `pre_settlement_window_minutes` | 30 | Measures displacement into funding settlement. | Captures short position-management flow before an 8-hour futures settlement event without becoming a broad trend regime. |
| `displacement_pct` | 0.35 percent | Minimum pre-settlement directional displacement. | Large enough to be a meaningful BTCUSDT/ETHUSDT futures displacement rather than ordinary 5m noise. |
| `hold_bars` | 3 | Fixed time exit after entry. | Targets the immediate post-settlement unwind over about 15 minutes. |

## 4. Fee and slippage assumptions

- Taker fee per side: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Slippage per side: 0.05 percent.
- Round-trip slippage buffer: 0.10 percent.
- Total round-trip friction assumption: approximately 0.18 percent.
- Funding: historical funding-rate values are excluded. Positions are intended to enter after settlement and exit after about 15 minutes, so they are not designed to cross the next 8-hour settlement.

No deviation from `obsidian/01_Rules/02_Fee_Slippage_Model.md`.

## 5. Execution model

- Minute data is consolidated into completed 5m bars.
- Signal is created after the first completed 5m bar after a 00:00, 08:00, or 16:00 UTC funding settlement.
- Entry order is submitted only when algorithm time is strictly greater than the signal bar timestamp.
- Exit order is submitted after 3 completed 5m bars from entry.
- BTCUSDT and ETHUSDT are evaluated independently; no cross-asset signal is used.

## 6. Expected trade count

- Per day per symbol: approximately 1 to 3 trades.
- Combined BTCUSDT and ETHUSDT: approximately 4 to 10 trades per day.
- Per 12-month OOS window: roughly 1,400 to 3,600 completed trades before missing-data and overlap exclusions.

## 7. Diagnostics plan

See `strategies/H0007_funding_settlement_unwind/diagnostics.md`.

## 8. Known risks and expected failure modes

- Pre-settlement displacement may be information-driven and continue after settlement.
- Actual funding-rate magnitude may be necessary, but H0007 does not use funding-rate history because QC-native availability is not confirmed.
- Reversal may happen inside the first post-settlement bar before delayed execution.
- BTCUSDT and ETHUSDT signals may cluster around the same macro event.
- Average raw reversal may be below the 0.18 percent round-trip friction assumption.
- QC Binance Futures symbol support or lot sizing may create invalid orders with 200 USDT starting capital.

## 9. Brokerage model verification step

QuantConnect Lean v17685 exposes Binance-related brokerage models and crypto futures subscriptions, but exact USD-M perpetual symbol mapping may vary. Before the first full backtest, the user must:

1. Open QuantConnect project 30774195.
2. Paste `strategies/H0007_funding_settlement_unwind/main.py`.
3. Run a 3-day smoke test that includes 00:00, 08:00, and 16:00 UTC.
4. Confirm:
   - BTCUSDT and ETHUSDT subscriptions load.
   - There are no brokerage-model unsupported warnings.
   - Fills happen with nonzero quantities if signals occur.
   - `execution_bar_time` is strictly later than `signal_bar_time` in every `ENTRY` and `TRADE` line.
5. If any of the above fails, do not proceed to the full backtest. Record the observed behavior and send it for code review.

## 10. Paste-ready code

See `strategies/H0007_funding_settlement_unwind/main.py`.
