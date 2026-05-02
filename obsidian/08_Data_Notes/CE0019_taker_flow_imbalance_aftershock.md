---
id: CE0019
slug: taker_flow_imbalance_aftershock
created: 2026-05-01
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
---

# CE0019 - taker_flow_imbalance_aftershock

## 1. Mechanism

Aggressive taker buy or sell imbalance in perpetual futures can show one-sided leveraged urgency before it is fully reflected in OHLC bars. If a large taker imbalance prints without equivalent price progress, the crowded aggressive side may be trapped; if price follows through, the imbalance can produce a short aftershock continuation. The candidate depends on derivatives-side signed flow, not on raw price momentum.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.10 to 0.18 percent if taker buy/sell volume is available at 1m or 5m resolution.
- Reasoning from first principles: signed aggressive flow is closer to the actual pressure source than OHLCV. A large imbalance can plausibly precede a move above the 0.10 percent pre-fee floor, but the edge is fragile and depends on clean flow timestamps.

## 3. Expected trade frequency per day per symbol

- BTCUSDT: approximately 2 to 6 trades per day.
- ETHUSDT: approximately 3 to 7 trades per day.
- Combined: approximately 5 to 12 trades per day if imbalance events are available.

## 4. Expected failure modes

- Taker imbalance marks exhaustion rather than continuation or trap.
- The move completes within the same bar and next-bar execution arrives too late.
- Taker buy/sell fields are unavailable or not reliable in QC.
- The signal needs both continuation and reversal branches, creating too many parameters.
- Raw aftershock moves are below the 0.18 percent round-trip friction assumption.

## 5. Data required

- Bars: 1m or 5m Binance USD-M Futures OHLCV bars for BTCUSDT and ETHUSDT.
- Derivatives features: taker buy volume, taker sell volume, or signed aggressive volume by timestamp.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: BLOCKED. Local notes confirm expected bar data only; they do not confirm native signed taker flow fields for Binance USD-M Futures.
- If unavailable: this candidate is blocked. Do not infer signed taker flow from candle color or volume.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, H0006, or H0002 because it does not use spot spread reclaim, wick proxies, same-symbol price microtrend, compression breakout, Bollinger/range mean reversion, or BTC-to-ETH price lag. It is not funding settlement unwind because it is event-driven by signed aggressive futures flow, not by the funding clock.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 1
- Code complexity, lower is better (1-5): 4
- Risk of disguised rejected mechanism, lower is better (1-5): 2
- Total: 14

## 8. Decision

- [ ] Promote to hypothesis.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0019_taker_flow_imbalance_aftershock.md` with reason.

Researcher decision: BLOCKED. Signed taker-flow history is not confirmed as QC-native in Lean v17685.
