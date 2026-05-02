---
id: H0002
slug: btc_perp_eth_lag
status: rejected
created: 2026-04-29
mechanism_class: lead_lag
symbols: [BTCUSDT, ETHUSDT]
timeframe: 5m
expected_trades_per_day: [5, 10]
free_parameters: [btc_impulse_pct, eth_max_samebar_move_pct, hold_bars]
---

# H0002 - btc_perp_eth_lag

## 1. Mechanism

BTCUSDT perpetual futures are the first crypto instrument many leveraged traders use for rapid risk transfer. A completed BTCUSDT perp impulse can precede a delayed ETHUSDT perp response as cross-crypto beta hedges and inventory adjustments propagate. The strategy hypothesis is to trade ETHUSDT in the direction of the completed BTCUSDT move only after the BTC signal bar is known, holding for a short fixed number of 5m bars.

## 2. Distinct-from-rejected statement

This hypothesis is not H0001 or H0006 because it is not a same-symbol spot mean-reversion, spread-reclaim, Bollinger, or range-filter setup. It is not H0003 because it does not use wick geometry or assume unavailable liquidation history. It is not H0004 because it does not trade BTC same-symbol microtrend with a trailing stop; it trades ETHUSDT perpetuals from a BTCUSDT perpetual lead-lag signal, with execution delayed until after the source bar timestamp is available.

## 3. Expected pre-fee edge

- Expected average pre-fee PnL per trade: 0.12 percent.
- Reasoning: a BTC 5m perp impulse of at least 0.35 percent can represent a broad crypto risk-transfer shock. If ETHUSDT has not already moved more than 0.12 percent in the same direction during that completed bar, the remaining beta catch-up over the next 1 to 3 bars can plausibly exceed 0.10 percent before fees. This is an a priori microstructure claim, not a backtest result.
- Must be >= 0.10 percent to pass the floor.

## 4. Expected trade frequency

- Per day per symbol: 5 to 10 ETHUSDT trades.
- Per backtest window (12 months OOS): roughly 1,250 to 2,500 ETHUSDT trades before any missing-data exclusions, assuming 250 active trading days equivalent in 24/7 crypto.
- Must plausibly reach >= 300 trades over the OOS window to satisfy criterion 1 of the framework.

## 5. Free parameters

- Name: btc_impulse_pct.
  Role: minimum completed 5m BTCUSDT return required to define a source impulse.
  Candidate value: 0.35 percent.
  Why this value is chosen a priori (not post hoc): this is large enough to avoid ordinary 5m noise on BTCUSDT while still occurring multiple times per day in active perpetual markets.

- Name: eth_max_samebar_move_pct.
  Role: maximum ETHUSDT same-direction move allowed during the BTC signal bar; if ETH already moved too much, the lag is considered spent.
  Candidate value: 0.12 percent.
  Why this value is chosen a priori (not post hoc): the hypothesis needs residual ETH catch-up. A same-bar ETH move above this level means ETH has probably already repriced and the delayed edge is weaker.

- Name: hold_bars.
  Role: fixed exit after entry, measured in 5m bars.
  Candidate value: 3.
  Why this value is chosen a priori (not post hoc): lead-lag effects should resolve quickly; 15 minutes is long enough for propagation but short enough to avoid turning the trade into a generic intraday trend position.

## 6. Expected failure modes

1. ETHUSDT reprices inside the same completed 5m bar as BTCUSDT, leaving no residual lag at the next executable bar.
2. BTCUSDT impulses caused by BTC-specific news do not propagate to ETHUSDT and create adverse selection.
3. Signals cluster during high-volatility periods, producing repeated entries into the same exhausted move.
4. The raw catch-up effect exists but averages below the 0.18 percent round-trip friction assumption.
5. QC symbol mapping or data alignment for Binance USD-M Futures prevents reliable synchronized BTCUSDT and ETHUSDT 5m bars.

## 7. Data required

- What data is used? BTCUSDT and ETHUSDT Binance USD-M Futures 5m bar data, constructed only from completed bars. No funding, open interest, basis, or liquidation history is used.
- Is it available in QC Lean v17685 for BTCUSDT and ETHUSDT? Partial / expected, not silently assumed. Local data notes say minute bars for BTCUSDT and ETHUSDT perpetuals are expected via the Crypto Futures dataset, but the engineer must verify exact QuantConnect Binance Futures symbol support before relying on it.
- If no: this hypothesis is blocked until an alternative source is approved.

## 8. Execution model

- Order type: market order on ETHUSDT perpetual futures, modeled with the default v1 taker-fee and slippage assumptions.
- Entry bar / exit bar rule: compute the signal from completed 5m BTCUSDT and ETHUSDT bars at timestamp T. If conditions pass, enter ETHUSDT at the next available ETHUSDT bar after T. Exit after `hold_bars` completed 5m bars.
- No-leakage statement: the BTCUSDT source bar and ETHUSDT comparison bar must both have timestamps strictly before the ETHUSDT execution bar. The strategy must log signal bar timestamp, execution bar timestamp, and positive delta for every trade.

## 9. Success / failure definition

- Success: criteria 1 to 6 all pass on OOS, then MC P5 final equity is above starting capital under the framework.
- Failure: any required criterion fails.
- Trade-count expectation over window: expected OOS trade count is above 300 if QC data is available and the BTC impulse threshold produces the estimated 5 to 10 trades per day.

## 10. Risk controls

- Position sizing rule: use the repository v1 isolated-margin constraint; the engineer must choose a fixed leverage within the allowed 2x to 3x range before code is written and document it in the strategy README. This researcher note does not add a tunable sizing threshold.
- Hard stop rule: no additional numeric hard stop in researcher mode, because adding one would exceed the three-parameter limit. Exit is controlled by the fixed `hold_bars` time exit.
- Daily loss cap: no additional numeric daily loss cap in researcher mode, because adding one would exceed the three-parameter limit. Intraday risk is constrained by isolated margin, fixed sizing, and the fixed time exit.

## 11. Links

- Candidate edge note: `obsidian/08_Data_Notes/CE0001_btc_perp_eth_lag.md`
- Strategy folder (after engineer): `strategies/H0002_btc_perp_eth_lag/`
- Backtest reports (after user run): `obsidian/04_Backtests/`

## Post-mortem

- Date of verdict: 2026-04-29.
- Hypothesis ID: H0002_btc_perp_eth_lag.
- Strategy ID: S0001_btc_perp_eth_lag.
- Backtest ID: BT0001_H0002_2026-04-29.
- Backtest report: `../04_Backtests/BT0001_H0002_2026-04-29/report.md`.
- Market: Binance USD-M Futures, BTCUSDT signal, ETHUSDT traded.
- Timeframe: 5m signal, ETH execution on next available bar, hold 3 completed ETH 5m bars.
- Devin verdict: FAIL / REJECTED.

### Observed metrics

- Start Equity: 200 USDT.
- End Equity: 170.78 USDT.
- Net Profit: -14.608%.
- Sharpe: -0.774.
- Drawdown: 28.3%.
- Win Rate: 31%.
- Loss Rate: 69%.
- Total Orders: 278.
- Approx completed trades: 132.
- Total Fees: 43.07 USDT.
- Profit-Loss Ratio: 1.90.
- Expectancy: -0.098.

### Failed criteria from Falsification Framework V3

- Trade count >= 300: FAIL, only 132 completed trades.
- OOS Sharpe > 1.0: FAIL, Sharpe -0.774.
- OOS net average trade > 0: FAIL, expectancy negative at -0.098.
- Max drawdown < 25 percent: FAIL, drawdown 28.3%.
- Pre-fee average >= 0.10 percent per trade: not proven / failed to establish from result.
- WR >= 50 percent or PF >= 1.25 with stable payoff ratio: FAIL. Win rate was 31%; PF / profit-loss ratio alone is not enough because net result and Sharpe failed.
- Monte Carlo P5 equity / P95 drawdown: NOT RUN because criteria 1-6 failed. Monte Carlo is not allowed after failed criteria 1-6.

### Technical issues

- Insufficient Buying Power order errors appeared.
- Some orders were invalid due to buying power.
- This is noted as a technical issue, but H0002 still fails on performance metrics even before considering this issue.

### Which a-priori assumption turned out wrong?

The a-priori assumption that a completed BTCUSDT 5m perpetual impulse would leave a reliable ETHUSDT residual catch-up over the next 3 completed ETH 5m bars did not hold in the full QuantConnect backtest. ETH often appeared to have already repriced, moved under a different regime, or failed to deliver enough residual movement after fees and slippage. The simple BTC-to-ETH lead-lag mechanism was not strong enough and produced too few completed trades for intraday validation.

### Forbidden follow-ups

- Do not rerun H0002 with a different BTC impulse threshold.
- Do not rerun H0002 with a different ETH same-bar threshold.
- Do not rerun H0002 with different holding bars.
- Do not add stop-loss or take-profit to H0002.
- Do not add time filter, cooldown, volatility filter, or extra confirmation filter to H0002.
- Do not change leverage to rescue H0002.
- Do not rebrand the same BTCUSDT to ETHUSDT 5m residual catch-up mechanism as a new hypothesis.

### Allowed future research

Only genuinely new hypotheses with a different mechanism are allowed, for example:

- funding regime strategy;
- open interest expansion/contraction strategy;
- basis/funding dislocation strategy;
- volatility compression to expansion strategy;
- higher timeframe futures regime strategy;
- BTC/ETH/SOL multi-asset futures regime with independent, pre-defined regime logic.

### Generalizable lesson

Create / link lesson: `../07_Lessons/L0002_simple_btc_eth_perp_lead_lag_failed.md`.

Simple BTCUSDT to ETHUSDT 5m perpetual lead-lag without an independent regime mechanism failed and must not be repeated as the same mechanism with parameter tuning.

### Related rejected IDs

- H0004: also failed as a short-horizon directional continuation idea, though H0002 was cross-asset perpetual lead-lag rather than same-symbol BTC spot microtrend.
