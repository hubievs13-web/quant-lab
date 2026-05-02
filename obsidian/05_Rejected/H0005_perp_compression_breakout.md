---
id: H0005
slug: perp_compression_breakout
status: rejected
created: 2026-04-29
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
timeframe: 5m
expected_trades_per_day: [6, 14]
free_parameters: [compression_bars, max_compression_range_pct, hold_bars]
---

# H0005 - perp_compression_breakout

## 1. Mechanism

Binance USD-M perpetuals can build clustered short-horizon stop and market-order liquidity around a tight range after leverage flow temporarily balances. If a completed 5m futures bar breaks out of that compressed range, the first expansion can trigger additional futures flow in the breakout direction. The hypothesis trades BTCUSDT and ETHUSDT perpetuals in the direction of a same-symbol compression breakout, with execution delayed until the next available bar.

## 2. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0006, or H0002. It is not spot spread reclaim, wick recovery, Bollinger/range mean reversion, or BTC-to-ETH lead-lag. It also differs from H0004 because it does not enter after consecutive same-direction bars or trail a microtrend; the required mechanism is a prior compressed futures range that resolves through its boundary, implying order-flow expansion after leverage balance.

## 3. Expected pre-fee edge

- Expected average pre-fee PnL per trade: 0.12 percent.
- Reasoning: a 5m close outside a tight 12-bar futures range can trigger stops and short-term market orders around the compression boundary. The expected raw continuation over the next 3 completed 5m bars is plausibly above 0.10 percent before fees, but this is an a priori mechanism claim and must be falsified by QuantConnect.
- Must be >= 0.10 percent to pass the floor.

## 4. Expected trade frequency

- Per day per symbol: 3 to 7 trades.
- Per backtest window (12 months OOS): roughly 1,500 to 3,500 combined BTCUSDT and ETHUSDT trades before overlap and missing-data exclusions.
- Must plausibly reach >= 300 trades over the OOS window to satisfy criterion 1 of the framework.

## 5. Free parameters

- Name: compression_bars.
  Role: number of completed 5m bars used to define the prior compression range.
  Candidate value: 12.
  Why this value is chosen a priori (not post hoc): 12 bars is one hour of 5m data, long enough to define a meaningful intraday range without turning the setup into a swing signal.

- Name: max_compression_range_pct.
  Role: maximum high-low range over the compression window, expressed as a percent of window midpoint.
  Candidate value: 0.35 percent.
  Why this value is chosen a priori (not post hoc): BTCUSDT and ETHUSDT perpetuals need a genuinely tight one-hour range for stop clustering; 0.35 percent is tight enough to avoid ordinary volatility but not so strict that trade count should collapse.

- Name: hold_bars.
  Role: fixed exit after entry, measured in completed 5m bars.
  Candidate value: 3.
  Why this value is chosen a priori (not post hoc): futures expansion after compression should resolve quickly; 15 minutes targets the first flow burst rather than a broad trend.

## 6. Expected failure modes

1. Breakouts from compression are false breaks and revert inside the prior range within one or two bars.
2. The compressed range identifies low-participation periods rather than stop clustering, so follow-through is too small.
3. BTCUSDT and ETHUSDT signals cluster at the same time and create correlated losses.
4. The average raw expansion is below the 0.18 percent round-trip friction assumption.
5. QC futures symbol mapping, fill model, or slippage model differs from Binance USD-M assumptions and makes results unreliable.

## 7. Data required

- What data is used? BTCUSDT and ETHUSDT Binance USD-M Futures 5m OHLC bars only. No funding, open interest, basis, liquidations, spot, CFD, or external data.
- Is it available in QC Lean v17685 for BTCUSDT and ETHUSDT? Yes / expected for Crypto Future price bars, with explicit verification required in QuantConnect before relying on the run. Current QuantConnect documentation lists Binance Crypto Future price data and examples using `add_crypto_future` for BTCUSDT / ETHUSDT, but the exact project symbol mapping must still be checked.
- If no: this hypothesis is blocked until an alternative source is approved.

## 8. Execution model

- Order type: market order on the same symbol that produced the compression breakout.
- Entry bar / exit bar rule: compute compression range and breakout from completed 5m bars at timestamp T. If a completed 5m close breaks above the prior compression high, enter long on the next available bar. If it breaks below the prior compression low, enter short on the next available bar. Exit after `hold_bars` completed 5m bars.
- No-leakage statement: the compression window and breakout bar must end strictly before the execution bar. No same-bar close signal is executed at the same-bar close.

## 9. Success / failure definition

- Success: criteria 1 to 6 all pass on OOS, then MC P5 final equity is above starting capital under the framework.
- Failure: any criterion fails.
- Trade-count expectation over window: expected OOS trade count is above 300 if QC futures data is available and the compression condition produces the estimated 6 to 14 combined trades per day.

## 10. Risk controls

- Position sizing rule: use isolated-margin assumption with fixed 2x leverage selected by the engineer within the repository v1 allowed range. This is a fixed implementation assumption, not an optimized parameter.
- Hard stop rule: no numeric stop-loss is added in researcher mode because it would add another parameter and would alter the mechanism.
- Daily loss cap: no numeric daily loss cap is added in researcher mode because it would add another parameter. Risk is constrained by fixed sizing and fixed time exit.

## 11. Links

- Candidate edge note: `obsidian/08_Data_Notes/CE0009_perp_compression_breakout.md`
- Strategy folder (after engineer): `strategies/H0005_perp_compression_breakout/`
- Backtest reports (after user run): `obsidian/04_Backtests/`

## Post-mortem

- Date of verdict: 2026-04-29.
- Hypothesis ID: H0005_perp_compression_breakout.
- Strategy package: `strategies/H0005_perp_compression_breakout/`.
- Backtest ID/name: Smooth Blue Jellyfish.
- Backtest period: 2024-01-01 to 2025-01-01.
- Market: Binance USD-M Futures / Crypto Futures, BTCUSDT and ETHUSDT.
- Timeframe: 5m compression breakout, same-symbol entry on next available bar, hold 3 completed 5m bars.
- External verdict: FAIL / REJECTED.

### Observed metrics

- Start Equity: 200.
- End Equity: 22.19.
- Net Profit: -88.903%.
- Sharpe Ratio: -6.013.
- Drawdown: 88.9%.
- Win Rate: 10%.
- Profit-Loss Ratio: 0.74.
- Expectancy: -0.818.
- Total Orders: 3392.
- Total Fees: 79.85.

### Failed criteria from Falsification Framework V3

- OOS Sharpe > 1.0: FAIL, Sharpe -6.013.
- OOS net average trade > 0: FAIL, net result and expectancy negative.
- Max drawdown < 25 percent: FAIL, drawdown 88.9%.
- Pre-fee average >= 0.10 percent per trade: failed to establish from result; strategy failed after realistic friction.
- WR >= 50 percent or PF >= 1.25 with stable payoff ratio: FAIL, win rate 10% and profit-loss ratio 0.74.
- Monte Carlo: NOT RUN because criteria 1-6 failed.

### Technical notes

- `ORDER_BLOCKED_ZERO_QTY` appeared for BTCUSDT because small starting capital and BTC lot size 0.001 prevented some BTC orders.
- QuantConnect log limit was reached.
- Overview statistics are sufficient for FAIL; the technical issues do not rescue the hypothesis.

### Which a-priori assumption turned out wrong?

The a-priori assumption that a tight 12-bar 5m futures range would resolve into durable short-horizon order-flow expansion did not hold. The backtest suggests the mechanism mostly captured false breakouts or low-quality volatility expansion, and realistic friction plus poor win rate overwhelmed any breakout payoff.

### Forbidden follow-ups

- Do not rerun H0005 with a different compression threshold.
- Do not rerun H0005 with different `compression_bars`.
- Do not rerun H0005 with different `hold_bars`.
- Do not add stop-loss, take-profit, cooldown, time filter, volatility filter, leverage changes, or sizing changes to rescue H0005.
- Do not rebrand simple same-symbol 5m Binance futures compression breakout as a new hypothesis.

### Generalizable lesson

Create / link lesson: `../07_Lessons/L0005_perp_compression_breakout_failed.md`.

Simple same-symbol 5m Binance USD-M futures compression breakout on BTCUSDT/ETHUSDT failed badly after realistic friction and must not be repeated via parameter tuning.

### Archival links

- Processed backtest report: `../04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/report.md`
- Lesson note: `../07_Lessons/L0005_perp_compression_breakout_failed.md`
