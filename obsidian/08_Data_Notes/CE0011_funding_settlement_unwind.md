---
id: CE0011
slug: funding_settlement_unwind
created: 2026-05-01
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
---

# CE0011 - funding_settlement_unwind

## 1. Mechanism

Binance USD-M perpetual futures have scheduled 8-hour funding settlements. Around those timestamps, some leveraged traders reduce or reopen positions to avoid paying funding, realize basis trades, or rebalance margin. If a contract is directionally displaced into the settlement timestamp, the post-settlement flow can unwind part of that displacement once the immediate funding event has passed. The candidate fades only the completed pre-settlement displacement and enters after the first post-settlement bar is known, so the edge comes from futures funding-calendar microstructure rather than a generic candle reversal.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.18 percent.
- Reasoning from first principles: funding settlement is a known futures-only event that can concentrate position management into a short window. A 30-minute directional displacement into settlement can plausibly include funding-avoidance flow and margin rebalancing that partially reverses after the event. The expected raw reversal over the next 15 minutes must be above the 0.10 percent pre-fee floor, but this is an a priori hypothesis and not a claim of profitability.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 1 to 3 trades per day.
- ETHUSDT: approximately 1 to 3 trades per day.
- Combined: approximately 4 to 10 trades per day, depending on how often the displacement threshold is met around the three daily settlement times.

## 4. Expected failure modes

- The pre-settlement displacement is caused by real information and continues after settlement instead of unwinding.
- Funding-avoidance flow is too small on BTCUSDT and ETHUSDT to overcome 0.18 percent round-trip friction.
- The effect only exists when the actual funding rate is extreme, but historical funding values are not available in v1.
- Signals cluster during major news releases that happen near funding timestamps.
- The reversal completes inside the first post-settlement bar before next-bar execution can participate.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: scheduled Binance USD-M funding settlement timestamps only. No historical funding rate values are used.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: partial / expected. Local data notes say minute bars for BTCUSDT and ETHUSDT perpetual futures are expected via the Crypto Futures dataset, but exact QuantConnect Binance Futures symbol mapping must be verified before implementation. Historical funding rate values are not required for this candidate.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, H0006, or H0002. It does not use spot spread reclaim, wick-based liquidation inference, same-symbol microtrend continuation, simple compression breakout, Bollinger/range mean reversion, or BTC-to-ETH lead-lag. The mechanism is scheduled perpetual funding-settlement position management; price displacement is only the observable input used to identify which side may have been pressured into the futures-only settlement event.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 4
- Total: 15

## 8. Decision

- [x] Promote to hypothesis as `H0007_funding_settlement_unwind.md`.
- [ ] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0011_funding_settlement_unwind.md`
      with reason. Never delete.
