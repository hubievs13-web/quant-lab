---
id: CE0007
slug: oi_expansion_continuation
created: 2026-04-29
mechanism_class: oi
symbols: [BTCUSDT, ETHUSDT]
---

# CE0007 - oi_expansion_continuation

## 1. Mechanism

When open interest expands sharply while price breaks out, the move may be driven by new leveraged positions rather than spot inventory transfer. A short continuation edge can exist if the new position build-up is not immediately absorbed. Conversely, price movement with falling OI can reflect short covering or long liquidation and may have weaker continuation.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.22 percent if reliable 5m or 15m OI snapshots are available.
- Reasoning from first principles: OI distinguishes new leveraged risk from position closing, which bar-only price cannot do. A breakout backed by fresh OI expansion can plausibly travel far enough to clear the 0.10 percent pre-fee floor, but only if OI timestamps are available before execution.

## 3. Expected trade frequency per day per symbol

- Approximately 3 to 8 trades per day per symbol if OI is available at 5m or 15m resolution.

## 4. Expected failure modes

- OI snapshots lag price so the signal arrives after the move is over.
- OI expansion reflects crowded late entries and marks exhaustion.
- OI data has missing intervals or timestamp ambiguity.
- The trade count is too low after requiring clean OI alignment.
- QC Lean v17685 lacks native Binance USD-M OI history.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: historical open interest snapshots.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no / not confirmed by local data notes. Treat as blocked in v1 unless QC-native OI history is explicitly verified.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0006, or H0002. It does not rely on spot mean reversion, wick proxies, same-symbol bar-count momentum, Bollinger rejection, or BTC-to-ETH residual catch-up. The specific mechanism is new leveraged position expansion measured by OI, which is a futures-only state variable.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 2
- Total: 11

## 8. Decision

- [ ] Promote to hypothesis. Not selected because required historical OI data is not confirmed in QC Lean v17685.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0007_oi_expansion_continuation.md`
      with reason. Never delete.
