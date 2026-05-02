---
id: H0007
slug: funding_settlement_unwind
status: rejected
created: 2026-05-01
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
timeframe: 5m
expected_trades_per_day: [4, 10]
free_parameters: [pre_settlement_window_minutes, displacement_pct, hold_bars]
---

# H0007 - funding_settlement_unwind

## 1. Mechanism

Binance USD-M perpetual futures settle funding every 8 hours. Around those scheduled timestamps, leveraged traders can reduce, flip, or reopen exposure to manage funding payments and margin. If BTCUSDT or ETHUSDT is directionally displaced into the settlement timestamp, part of that move may unwind after the immediate funding-related flow has passed.

## 2. Why the edge should exist

Funding settlement is a futures-only recurring event that can concentrate position-management flow into a short window. A large pre-settlement move can include traders exiting the paying side, basis desks rebalancing, or late leveraged flow reacting to funding risk. Once settlement is complete, the forced timing pressure can disappear, making a partial reversal over the next few 5m bars plausible. The expected edge is not assumed to come from leverage, and leverage is not the source of the signal.

## 3. Why this is futures-specific

Spot markets do not have perpetual funding payments or an 8-hour funding settlement clock. This hypothesis uses the Binance USD-M funding schedule as the market-structure event and uses futures bars only to observe the displacement into that event. It does not require historical funding-rate values, open interest, basis, or liquidation feeds.

## 4. Distinct-from-rejected statement

H0007 is not H0001 because it is not ETH spot spread reclaim or mid-price normalization. It is not H0002 because it does not use BTCUSDT to trade ETHUSDT or any cross-asset lead-lag residual catch-up. It is not H0003 because it does not infer liquidations from wick geometry and does not require liquidation history. It is not H0004 because it does not trade same-symbol microtrend continuation or use a trailing stop. It is not H0005 because it does not trade simple same-symbol compression breakout. It is not H0006 because it does not fade Bollinger bands or a generic range-filter mean-reversion pattern. The mechanism is scheduled perpetual funding-settlement position management.

## 5. Symbols

- BTCUSDT Binance USD-M perpetual futures.
- ETHUSDT Binance USD-M perpetual futures.
- SOLUSDT is not used because BTCUSDT and ETHUSDT are sufficient for v1 and have the strongest expected QC support.

## 6. Timeframe

- Signal bars: completed 5m Binance USD-M Futures bars.
- Entry and exit timing: next available 5m bar or later.
- Funding settlement clock: Binance USD-M convention of 00:00, 08:00, and 16:00 UTC.

## 7. Entry logic in prose only

For each symbol independently, observe the completed 5m bars ending before a scheduled funding settlement timestamp. If the close immediately before settlement is displaced upward by at least `displacement_pct` from the close at the start of the `pre_settlement_window_minutes`, the candidate direction is short. If the close immediately before settlement is displaced downward by at least `displacement_pct`, the candidate direction is long. No trade is entered before settlement. After the first completed 5m bar after settlement is available, enter in the reversal direction on the next available bar only if no position is already open in that symbol.

## 8. Exit logic in prose only

Exit after `hold_bars` completed 5m bars from entry. There is no numeric stop-loss, take-profit, or trailing stop in the researcher definition because those would add parameters and turn the idea into post-hoc trade management. If a new opposite settlement signal appears while a position is open, ignore it until the current time exit completes.

## 9. Execution timing and no-leakage rule

Signal bar t is the first completed 5m bar after the funding settlement timestamp plus the already completed pre-settlement window. Execution occurs on bar t+1 or later. The displacement window, settlement timestamp, and first post-settlement confirmation bar must all have timestamps strictly before the execution timestamp. Multi-symbol signals are not used to trade another symbol; BTCUSDT and ETHUSDT are evaluated independently, so no cross-asset same-bar leakage is introduced.

## 10. Expected pre-fee edge

- Expected average pre-fee PnL per trade: 0.12 percent.
- Reasoning: the setup requires a meaningful directional displacement into a futures-only settlement event, then waits until settlement has passed before fading the pressured side. A partial reversal of roughly one third to one half of a 0.35 percent pre-settlement displacement can clear the 0.10 percent pre-fee floor before costs. This is a falsifiable a priori mechanism claim, not a profitability claim.
- Required floor: expected pre-fee average trade must be at least 0.10 percent.

## 11. Expected trade frequency

- Per day per symbol: approximately 1 to 3 trades.
- Combined BTCUSDT and ETHUSDT: approximately 4 to 10 trades per day.
- Over a 12-month OOS window: roughly 1,400 to 3,600 combined completed trades before missing-data and overlap exclusions, so the setup should plausibly exceed the 300-trade intraday validation threshold if QC futures bars are available.

## 12. Free parameters

1. Name: `pre_settlement_window_minutes`.
   Role: length of completed history used to measure directional displacement into funding settlement.
   Candidate value: 30.
   A priori reason: 30 minutes is long enough to capture position-management flow before an 8-hour settlement event while staying intraday and avoiding broad trend classification.

2. Name: `displacement_pct`.
   Role: minimum absolute move from the start of the pre-settlement window to the last completed close before settlement.
   Candidate value: 0.35 percent.
   A priori reason: this is large enough to represent a meaningful short-horizon BTCUSDT or ETHUSDT futures displacement, not ordinary 5m noise, while still plausibly occurring around several settlements per day across two symbols.

3. Name: `hold_bars`.
   Role: fixed time exit measured in completed 5m bars after entry.
   Candidate value: 3.
   A priori reason: settlement-related unwind should be short-lived; 15 minutes targets the immediate post-event flow and avoids converting the hypothesis into generic intraday reversal.

## 13. Data required and availability confirmation

- Required data: BTCUSDT and ETHUSDT Binance USD-M Futures 5m OHLC bars, plus wall-clock timestamps for the known funding settlement schedule.
- Historical funding rates: not required.
- Open interest: not required.
- Basis / mark / index data: not required.
- Liquidation data: not required.
- Availability in QC Lean v17685: price bars for BTCUSDT and ETHUSDT perpetual futures are expected per local data notes via QuantConnect Crypto Futures data, but exact Binance Futures symbol mapping must be verified in QuantConnect before implementation. Because this hypothesis does not need funding-rate history, OI, basis, or liquidation history, no unavailable derivatives feature is required.

## 14. Fee and slippage assumptions

- Binance futures taker fee: 0.04 percent per side.
- Round-trip taker fee: 0.08 percent.
- Total round-trip friction assumption: approximately 0.18 percent after adding slippage and market-impact buffer.
- No maker rebate is assumed.
- Funding payments are not explicitly modeled in the hypothesis because positions are entered after settlement and held for about 15 minutes, so they are not intended to cross the next 8-hour settlement.

## 15. Expected failure modes

1. The pre-settlement displacement is information-driven and continues after settlement.
2. Actual funding-rate magnitude is necessary to identify the pressured side, but funding-rate history is unavailable in v1.
3. Reversal happens inside the first post-settlement bar and is missed by next-bar execution.
4. BTCUSDT and ETHUSDT signals cluster around the same macro event, creating correlated losses.
5. Average raw reversal is below the 0.18 percent round-trip friction assumption.
6. QC Binance Futures symbol support or minimum lot sizing creates invalid orders for the USD 200 starting-capital assumption.

## 16. Research outcome definition

- A valid research result would need the external review workflow to evaluate criteria 1 to 6 on OOS results and then Monte Carlo only if criteria 1 to 6 clear.
- Any required criterion not clearing would reject the hypothesis under the framework.
- Expected OOS trade count should be above 300 if the estimated 4 to 10 combined trades per day materializes.

## 17. Risk controls

- Position sizing rule: fixed fractional exposure using isolated margin only, with leverage capped at 2x to 3x per AGENTS.md. Leverage must not be used to create the edge.
- Hard stop rule: no separate numeric stop-loss in the researcher definition.
- Daily loss cap: no separate numeric daily loss cap in the researcher definition.
- Overlap rule: one open position per symbol; new same-symbol signals are ignored while a position is open.

## 18. Researcher self-audit checklist

- [x] Futures-specific mechanism: scheduled Binance USD-M perpetual funding settlement.
- [x] No historical funding, OI, basis, or liquidation data assumed.
- [x] Required market data limited to expected QC-native BTCUSDT and ETHUSDT futures bars plus timestamps.
- [x] Free parameters count is 3.
- [x] Expected pre-fee edge is at least 0.10 percent and justified a priori.
- [x] Fee/slippage assumption uses 0.04 percent taker fee per side and approximately 0.18 percent total round-trip friction.
- [x] No same-bar close signal with same-close execution.
- [x] Execution is next-bar or later after all signal inputs are known.
- [x] Distinct from H0001, H0002, H0003, H0004, H0005, and H0006.
- [x] No strategy code written in this note.
- [x] No profitability claim made.

## 19. Links

- Candidate edge note: `obsidian/08_Data_Notes/CE0011_funding_settlement_unwind.md`
- Strategy folder (after engineer): `strategies/H0007_funding_settlement_unwind/`
- Backtest reports (after user run): `obsidian/04_Backtests/`

---

## Post-mortem

- Date of verdict: 2026-05-01.
- Backtest report: not created in this recording pass. QuantConnect backtest name: Determined Orange Mule.
- Hypothesis ID: H0007_funding_settlement_unwind.
- Strategy ID: S0007_funding_settlement_unwind.
- Period: 2024-01-01 to 2025-01-01.
- Devin / ChatGPT verdict: FAIL / REJECTED.

### Failed criteria from framework V3

- Trade count >= 300: passed, approximately 509 completed trades.
- OOS Sharpe > 1.0: failed, Sharpe -5.112.
- OOS net average trade > 0: failed, average post-fee trade -0.1602 percent.
- Max drawdown < 25 percent: failed, max drawdown 48.900 percent.
- Pre-fee average trade >= 0.10 percent: failed, average pre-fee trade -0.0802 percent.
- WR >= 50 percent or PF >= 1.25 with stable payoff ratio: failed, win rate 32 percent and profit factor 0.73.
- Monte Carlo: not run because criteria 1-6 did not pass.

### Observed metrics

- Starting equity: 200.00 USDT.
- Ending equity: 102.62 USDT.
- Net Profit: -48.692 percent.
- Sharpe: -5.112.
- Max Drawdown: 48.900 percent.
- Total Orders: 1018.
- Approx completed trades: 509.
- Win Rate: 32 percent.
- Profit-Loss Ratio / Profit Factor: 0.73.
- Expectancy: -0.450.
- Total Fees: 48.32 USDT.
- Average pre-fee trade from trades.csv: -0.0802 percent.
- Average post-fee trade from trades.csv: -0.1602 percent.

### Technical notes

- H0007 compiled and ran.
- BTCUSDT and ETHUSDT loaded as CryptoFuture.
- SIGNAL, ENTRY, TRADE, and EXIT_ORDER_SUBMITTED logs existed.
- No same-bar execution was observed in sampled logs: execution_bar_time was later than signal_bar_time.
- Failure is recorded as research / mechanism failure, not a technical smoke-test failure.

### Which a-priori assumption turned out wrong?

The a-priori assumption that scheduled Binance USD-M funding settlement would create a short-lived, tradable post-settlement unwind after a 30-minute pre-settlement displacement did not hold. The completed backtest showed negative average pre-fee and post-fee trades, low win rate, poor payoff ratio, and excessive drawdown. The funding-settlement clock alone was not enough to identify a futures-specific edge without actual funding-rate, basis, or open-interest context.

### Generalizable lesson

Create / link lesson: `../07_Lessons/L0006_funding_settlement_unwind_failed.md`.

Scheduled funding-settlement timing plus bar-only pre-settlement displacement is not sufficient as a standalone Binance USD-M intraday edge on BTCUSDT and ETHUSDT.

### Forbidden follow-ups

- Do not rerun H0007 with a different pre-settlement window.
- Do not rerun H0007 with a different displacement threshold.
- Do not rerun H0007 with different holding bars.
- Do not add stop-loss, take-profit, trailing stop, cooldown, volatility filter, trend filter, leverage changes, or sizing changes to rescue H0007.
- Do not rebrand scheduled funding-settlement bar-only unwind as a new hypothesis.
- Do not add funding-rate, OI, basis, or liquidation filters unless a genuinely new hypothesis is filed and the required data availability is confirmed.

### Related rejected IDs

- H0005: also failed as a bar-only Binance USD-M futures short-horizon structure without confirmed derivatives state variables.
- H0006 and H0001: different mechanisms, but H0007 similarly failed to produce positive pre-fee average trade after realistic friction.
