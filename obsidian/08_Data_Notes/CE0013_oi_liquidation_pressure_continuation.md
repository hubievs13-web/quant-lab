---
id: CE0013
slug: oi_liquidation_pressure_continuation
created: 2026-05-01
mechanism_class: oi
symbols: [BTCUSDT, ETHUSDT]
---

# CE0013 - oi_liquidation_pressure_continuation

## 1. Mechanism

A sharp price move with falling open interest can indicate forced position closing rather than fresh risk-taking. If price continues after open interest contracts, the remaining forced flow may extend for several bars. The edge would use OI to distinguish liquidation or covering pressure from ordinary price momentum.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.22 percent if reliable OI snapshots are available.
- Reasoning from first principles: open interest is a direct futures state variable that helps identify whether price movement is backed by new leverage or forced position reduction. Forced de-risking can plausibly create raw moves above the 0.10 percent floor, but the signal cannot be tested honestly without historical OI.

## 3. Expected trade frequency per day per symbol

- Approximately 2 to 6 trades per day per symbol if 5m or 15m OI snapshots are available and timestamp-aligned.

## 4. Expected failure modes

- OI snapshots arrive too late and describe a move that has already completed.
- Falling OI marks exhaustion rather than continuation.
- OI data is missing, delayed, or not native to QC Lean v17685.
- The signal requires more than three thresholds to separate OI regimes cleanly.
- Trade count falls below the intraday validation minimum after strict timestamp alignment.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: historical open interest snapshots with timestamps known before execution.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no / not confirmed by local data notes. Treat as BLOCKED in v1 unless QC-native OI history is explicitly verified.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0005, H0006, or H0002. It does not use spot spread reclaim, wick proxies, same-symbol microtrend counts, compression breakout, Bollinger rejection, or cross-asset lead-lag. The mechanism is open-interest-confirmed forced positioning pressure, a futures-only data source, but the required data is unavailable under the current v1 notes.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 4
- Data availability (1-5): 1
- Simplicity (1-5, higher is simpler): 2
- Total: 11

## 8. Decision

- [ ] Promote to hypothesis. BLOCKED because required historical open interest is not confirmed in QC Lean v17685.
- [x] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0013_oi_liquidation_pressure_continuation.md`
      with reason. Never delete.
