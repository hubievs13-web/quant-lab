---
id: H0008
slug: funding_premium_crowding_unwind
status: draft
created: 2026-05-02
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
timeframe: 5m
expected_trades_per_day: [5, 12]
free_parameters: [funding_regime_abs_threshold, premium_compression_pct, hold_bars]
---

# H0008 - funding_premium_crowding_unwind

## 1. Mechanism

Binance USD-M perpetuals expose a real settled funding rate that identifies which leveraged side has recently paid for exposure. A persistent positive funding regime suggests crowded longs; a persistent negative funding regime suggests crowded shorts. If the premium index then compresses against that crowded side while only completed bars are used, the market may be starting a crowding unwind that can move last-trade perp price by more than ordinary 5m noise.

This hypothesis is futures-specific because it requires actual settled funding history and premium-index pressure. The edge is not the scheduled funding clock and not an OHLCV pattern; it is the interaction between observed funding regime and point-in-time premium compression.

## 2. Distinct-from-rejected statement

H0008 is not H0001 because it is not ETH spot spread reclaim or mid-price normalization. It is not H0002 because it does not use BTCUSDT to trade ETHUSDT or any cross-asset residual catch-up. It is not H0003 because it does not infer liquidation cascades from wick geometry and does not use liquidation data. It is not H0004 because it is not same-symbol 1m microtrend continuation or trailing-stop momentum. It is not H0005 because it does not trade a simple same-symbol compression breakout from OHLCV; premium compression is a required derivatives state variable and funding regime is required. It is not H0006 because it does not fade Bollinger bands or ordinary range-filter mean reversion. It is not H0007 because it does not trade scheduled funding-settlement timing or pre-settlement displacement; settled funding is used only after its timestamp as a regime variable, with premium confirmation.

## 3. Expected pre-fee edge

- Expected average pre-fee PnL per trade: 0.12 to 0.18 percent.
- Reasoning: a funding regime identifies a recently expensive leveraged side, and premium compression indicates that the perp-reference pressure is already starting to reverse. When both agree, the expected raw move can plausibly exceed 0.10 percent because the trade targets a leveraged crowd unwind rather than ordinary 5m bar noise. The claim is a priori and must be falsified; no backtest result is implied.
- Must be >= 0.10 percent to pass the floor.

## 4. Expected trade frequency

- Combined BTCUSDT and ETHUSDT: approximately 5 to 12 trades per day.
- Per symbol: approximately 2 to 6 trades per day.
- Per 12-month OOS window: roughly 1,800 to 4,300 combined candidate trades before overlap and no-signal exclusions, so the setup should plausibly exceed the 300-trade intraday validation threshold if later implemented.

## 5. Free parameters

1. Name: `funding_regime_abs_threshold`.
   Role: minimum absolute settled funding rate required to define a crowded funding regime.
   Candidate value: 0.01 percent.
   Why this value is chosen a priori: 0.01 percent is a common baseline funding magnitude on Binance USD-M perpetuals; requiring at least this level avoids treating near-zero funding as meaningful crowding.

2. Name: `premium_compression_pct`.
   Role: minimum completed-bar premium-index compression against the crowded side required to confirm pressure reversal.
   Candidate value: 0.015 percent.
   Why this value is chosen a priori: premium index values are smaller than last-price returns, so the threshold must detect a meaningful premium move without requiring a last-price breakout. It is intended to identify a visible change in perp-reference pressure, not ordinary tick noise.

3. Name: `hold_bars`.
   Role: fixed exit after entry, measured in completed 5m bars.
   Candidate value: 3.
   Why this value is chosen a priori: a crowding unwind driven by premium compression should resolve quickly; 15 minutes targets the first repricing window and avoids converting the idea into a broad trend or swing strategy.

## 6. Expected failure modes

1. Funding remains extreme during a strong directional trend, so fading the crowded side repeatedly loses.
2. Premium compresses only after last price already repriced, leaving no next-bar edge.
3. Settled funding is stale because it updates discretely and may not represent current intraday positioning pressure.
4. BTCUSDT and ETHUSDT signals cluster during market-wide deleveraging or macro shocks, creating correlated drawdowns.
5. The raw unwind exists but averages below the 0.10 percent pre-fee floor or below the 0.18 percent round-trip friction assumption.
6. Later QuantConnect implementation may require custom data plumbing that is not yet authorized.

## 7. Data required

- Allowed datasets used: `um_klines_1m`, `funding_rate_history`, `premium_index_klines`.
- Optional sanity datasets allowed but not required for the hypothesis definition: `mark_price_klines`, `index_price_klines`.
- Symbols: BTCUSDT and ETHUSDT only.
- Bar resolution: completed 1m source rows aggregated into completed 5m decision bars if implemented later.
- Data availability: available in local audited TIER 1 data under DL0008 for BTCUSDT and ETHUSDT from 2024-01-01 to 2026-05-02T07:19:00Z, with the DL0007 no-fill/no-signal exception.
- QuantConnect Lean v17685 native availability: not assumed. If the hypothesis passes ChatGPT review, any later engineering step must explicitly decide how audited TIER 1 data is made available to QuantConnect. This note does not authorize QuantConnect custom data.

## 8. Execution model

- Order type: market order in the same symbol that produced the signal, if later implemented.
- Conceptual entry logic: for each symbol independently, use only completed 5m bars. If the latest available settled funding regime is positive and above `funding_regime_abs_threshold`, require completed premium compression downward by at least `premium_compression_pct`; candidate direction is short. If the funding regime is negative and below negative `funding_regime_abs_threshold`, require completed premium compression upward by at least `premium_compression_pct`; candidate direction is long. Enter no earlier than the next bar after all source values are known.
- Conceptual exit logic: exit after `hold_bars` completed 5m bars from entry. No stop-loss, take-profit, trailing stop, cooldown, or volatility filter is part of the researcher definition.
- No-leakage execution model: source values must have source timestamps at or before the completed signal timestamp. Signals use completed bars only. Execution is at bar t+1 or later. No same-bar close-to-close execution is allowed. Funding values are usable only after their own `timestamp_utc`. DL0007 missing timestamps and any dependent 5m bars requiring complete price-state source data are no-signal. BTCUSDT and ETHUSDT are evaluated independently; no cross-symbol signal is used to trade the other symbol.

## 9. Success / failure definition

- Success: criteria 1 to 6 of Falsification Framework V3 all pass on OOS, then Monte Carlo P5 final equity must be above starting capital and the other MC conditions must pass.
- Failure: any required criterion fails.
- Trade-count expectation: expected OOS trade count should be above 300 if the 5 to 12 combined trades/day estimate materializes.

## 10. Risk controls

- Position sizing rule: later implementation must use fixed exposure with isolated margin constraints and 2x to 3x maximum leverage per AGENTS.md. Leverage is not a source of edge.
- Hard stop rule: no separate numeric stop-loss in the researcher definition because it would add another parameter and alter the mechanism.
- Daily loss cap: no separate numeric daily loss cap in the researcher definition because it would add another parameter. Risk is constrained by fixed sizing, one open position per symbol, and fixed time exit.
- Overlap rule: at most one open position per symbol; new same-symbol signals are ignored while a position is open.

## 11. Fee and slippage assumptions

- Binance futures taker fee: 0.04 percent per side.
- Round-trip taker fee: 0.08 percent.
- Total round-trip friction assumption: approximately 0.18 percent after slippage and market-impact buffer.
- Funding payments must be accounted for later if any position crosses a funding timestamp. The researcher concept targets short intraday holds but does not assume funding cost is zero if a hold crosses settlement.

## 12. Researcher self-audit checklist

- Uses only audited TIER 1 data: yes.
- Respects DL0007 no-fill/no-signal policy: yes.
- Mechanism distinct from H0001-H0007: yes, see section 2.
- Expected pre-fee edge >= 0.10 percent: yes, justified a priori in section 3.
- Free parameters <= 3: yes, exactly 3.
- No leakage by design: yes, completed bars, next-bar execution, funding after timestamp, DL0007 no-signal rows.
- No strategy code written: yes.
- No backtest run: yes.
- No QuantConnect custom data created: yes.

## 13. Links

- Candidate edge note: `obsidian/08_Data_Notes/CE0021_funding_premium_crowding_unwind.md`
- Strategy folder (after engineer, not created now): `strategies/H0008_funding_premium_crowding_unwind/`
- Backtest reports (after user run, not created now): `obsidian/04_Backtests/`
