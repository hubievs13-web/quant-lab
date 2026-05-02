---
id: S0001
hypothesis: H0002
slug: btc_perp_eth_lag
created: 2026-04-29
status: draft
---

# S0001 - btc_perp_eth_lag (implements H0002)

## 1. Link to hypothesis

`obsidian/02_Hypotheses/H0002_btc_perp_eth_lag.md`

## 2. Mechanism summary

BTCUSDT perpetual futures can lead short crypto risk-transfer moves. H0002 trades ETHUSDT perpetual futures only after a completed BTCUSDT 5m impulse if ETHUSDT has not already moved enough in the same completed 5m bar. The position is held for exactly 3 completed ETHUSDT 5m bars.

## 3. Free parameters (<= 3)

| Name | Value | Role | Justification |
|------|-------|------|---------------|
| btc_impulse_pct | 0.35 percent | Minimum completed BTCUSDT 5m move. | Large enough to avoid ordinary 5m noise while still expected several times per day. |
| eth_max_samebar_move_pct | 0.12 percent | Maximum same-direction ETHUSDT move during the BTC signal bar. | Keeps only cases where ETHUSDT has not already fully repriced. |
| hold_bars | 3 | Fixed holding period in completed ETHUSDT 5m bars. | Lead-lag effects should resolve quickly; 15 minutes avoids turning this into generic trend following. |

No stop-loss, take-profit, volatility filter, time-of-day filter, volume filter, cooldown, funding filter, OI filter, or optimizer is added.

## 4. Fee and slippage assumptions

- Taker fee per side: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Slippage model in `main.py`: 0.05 percent per side.
- Total round-trip friction assumption: approximately 0.18 percent.
- `post_fee_estimate_pct` subtracts only the 0.08 percent taker round-trip fee because slippage should already be reflected in fill prices if QC applies the slippage model.
- `full_friction_reference_pct` subtracts the full 0.18 percent round-trip friction as a conservative diagnostic reference.
- Funding: excluded. The planned holding period is 15 minutes, but if trades cross an 8-hour funding timestamp, QuantConnect may not model the funding payment exactly. Treat this as a limitation.
- Leverage: fixed at 2x, within the repository rule of 2x to 3x.
- Margin assumption: isolated margin is the intended real-exchange assumption. QuantConnect may model margin differently; verify brokerage and margin logs before relying on the run.

If QuantConnect does not apply `BinanceTakerFeeModel` or `ConstantBpsSlippageModel` as expected to crypto futures, the run must be treated as a diagnostic run until fees and fills are verified.

## 5. Distinct from rejected hypotheses

This is not H0001 or H0006 because it is not same-symbol spot mean reversion, spread reclaim, Bollinger rejection, or range filtering. It is not H0003 because it does not infer liquidations from wick geometry and does not require liquidation history. It is not H0004 because it does not trade BTC same-symbol microtrend; it trades ETHUSDT perpetual futures from a completed BTCUSDT perpetual lead-lag signal with delayed execution.

## 6. Execution model and no-leakage design

- Data used: BTCUSDT and ETHUSDT Binance USD-M Futures minute bars consolidated to 5m bars.
- Signal timestamp T: both BTCUSDT and ETHUSDT 5m bars must be completed and share the same `EndTime`.
- Long rule: BTCUSDT 5m return is at least +0.35 percent and ETHUSDT same-bar return is no more than +0.12 percent.
- Short rule: BTCUSDT 5m return is at most -0.35 percent and ETHUSDT same-bar return is no more than 0.12 percent in the same downward direction, implemented as ETHUSDT return >= -0.12 percent.
- Entry: only on the next available ETHUSDT minute bar whose timestamp is strictly greater than T.
- Exit: after exactly 3 completed ETHUSDT 5m bars.
- The strategy does not use future bars, same-bar close execution, external data, spot data, CFD data, funding, open interest, liquidations, or web requests.
- Per trade, logs include BTC signal timestamp, ETH comparison timestamp, ETH execution timestamp, BTC impulse percent, ETH same-bar move percent, direction, entry price, exit price, holding bars, exit reason, pre-fee PnL estimate, post-fee estimate, and full-friction reference PnL.

## 7. Expected trade count

- Expected ETHUSDT trades per day: 5 to 10 when BTC impulse conditions are active.
- Expected 12-month OOS trade count: roughly 1,250 to 2,500 before missing-data exclusions.
- Framework minimum for intraday strategies: at least 300 OOS trades.

## 8. Known risks and expected failure modes

- ETHUSDT may already reprice inside the same completed 5m bar, leaving no residual lag.
- BTCUSDT impulses may be BTC-specific and may not propagate to ETHUSDT.
- Signals may cluster during high volatility, causing repeated exposure to the same exhausted move.
- The raw catch-up effect may average below the 0.18 percent round-trip friction model.
- QuantConnect symbol mapping for Binance USD-M Futures may differ from the assumed `AddCryptoFuture("BTCUSDT"/"ETHUSDT", market=Market.BINANCE)` usage.
- Fee, slippage, and isolated-margin behavior for Binance Futures may not exactly match live Binance USD-M trading.
- Quantity can be zero if QC symbol lot size is incompatible with USD 200 cash at 2x notional; if so, treat it as a data/modeling blocker, not a reason to change the hypothesis.

## 9. Brokerage model verification step

QuantConnect Lean v17685 support for exact Binance USD-M Futures symbols and brokerage enums must be verified before a full backtest.

Manual verification:

1. Open QuantConnect project 30774195.
2. Paste `strategies/H0002_btc_perp_eth_lag/main.py` into `main.py`.
3. Run a short 3-day compile/backtest smoke test first.
4. Confirm the logs contain `INIT H0002 btc_perp_eth_lag`.
5. Confirm BTCUSDT and ETHUSDT are futures/perpetual symbols, not spot, CFD, or proxy data.
6. Confirm no warning says the brokerage model does not support the symbols.
7. Confirm fee/slippage model logs and order fills are present.
8. Confirm `SIGNAL`, `ENTRY_SUBMITTED`, `ENTRY_FILLED`, and `TRADE_EXIT` lines have strictly increasing signal and execution timestamps.
9. If Binance Futures BTCUSDT/ETHUSDT 5m bars are unavailable, mark this strategy BLOCKED. Do not replace with spot.

Known API uncertainties in `main.py`:

- `BrokerageName.BINANCE` is the current documented brokerage enum for Binance Crypto Futures examples, but the user should still verify it in Lean v17685.
- `add_crypto_future(..., market=Market.BINANCE, fill_forward=False, leverage=2)` may need a Lean-specific argument form.
- `BTCUSDT` and `ETHUSDT` may require a different ticker format for Binance USD-M perpetuals.
- `AccountType.MARGIN` may not fully represent isolated margin; isolated margin must be documented as an assumption.

## 10. Manual QuantConnect workflow

1. Paste `main.py` into the QC web IDE.
2. First run a 3-day smoke test only to verify symbol mapping, brokerage support, fees, and logs.
3. If the smoke test confirms Binance USD-M Futures support, run the full configured backtest.
4. Do not tune parameters after seeing results.
5. Export artifacts for Devin review:
   - Overview screenshot.
   - Equity curve screenshot.
   - `trades.csv` if available.
   - `orders.csv` if available.
   - `logs.txt`.
   - Statistics/report export if available.

## 11. Diagnostics plan

See `diagnostics.md`.

## 12. Paste-ready code

See `strategies/H0002_btc_perp_eth_lag/main.py`.
