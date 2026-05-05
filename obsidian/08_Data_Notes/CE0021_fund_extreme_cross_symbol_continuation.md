---
id: CE0021
slug: fund_extreme_cross_symbol_continuation
created: 2026-05-05
mechanism_class: funding
symbols: [BTCUSDT, ETHUSDT]
profile: B-Position
execution_tier: M
---

# CE0021 - fund_extreme_cross_symbol_continuation

## 1. Mechanism

Binance USD-M funding extremes can mark a persistent leveraged
positioning regime rather than an immediate reversal point. When
funding is extreme, the dominant crowded side may continue to press
directionally over the next several days because basis desks,
funding-sensitive carry traders, and leveraged trend participants are
not forced to unwind at the same timestamp. The candidate trades in the
event direction on BTCUSDT and ETHUSDT over the h+72 horizon.

## 2. Expected pre-fee edge per trade

- Estimate (percent): BTCUSDT approximately 1.08 percent; ETHUSDT
  approximately 0.96 percent.
- Reasoning from first principles: the displayed Tier M net edge in
  `research_candidates.md` is already after the 0.08 percent maker
  round-trip friction. Adding that friction back gives approximate
  pre-fee edge of 1.08 percent for BTCUSDT and 0.96 percent for
  ETHUSDT, both comfortably above the Tier M floor.
- Floor for the declared execution tier:
  - Tier T: >= 0.30 percent;
  - Tier M: >= 0.20 percent.
- Quoted Data Layer evidence (path + numeric line):
  - file: `data_layer/reports/summaries/research_candidates.md`
  - line: "| M | long | 1h | FUND_EXTREME | h+72 | 156 | +1.00% | 0.021 | 136 | +0.88% | 0.066 |"

## 3. Expected trade frequency per day per symbol

- This is a B-Position candidate, so frequency is measured per week,
  not per day.
- Actual event count in the cited Data Layer line is BTC n=156 and ETH
  n=136 over roughly 3 years, or 292 total events / 156 weeks =
  approximately 1.87 combined events per week. The fee budget uses 2
  trades per week as requested.
- This is below the nominal B-Position target of 5 to 15 trades per
  week and must be called out during pre-backtest audit.

## 4. Expected failure modes

1. Funding extremes are continuation markers only in the 365-day Data
   Layer window but reverse in a longer validation window.
2. Funding payments during a 72-hour hold offset part of the price edge
   and reduce net expectancy below the Tier M floor.
3. BTCUSDT and ETHUSDT events cluster during the same macro regimes,
   causing correlated drawdowns despite cross-symbol evidence.
4. Limit orders selected by the maker adverse-selection rule may fill
   only in worse sub-samples, reducing the realised edge below the
   summary net.
5. The actual trade count may be too low for the intended profile target,
   even if it clears the swing minimum trade-count criterion.

## 5. Data required

- Bars: BTCUSDT and ETHUSDT Binance USD-M Futures 1h bars, with
  completed bars only.
- Derivatives features: historical funding rate series sufficient to
  classify `FUND_EXTREME` at the event timestamp.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: no native QC
  funding history is assumed. The current local Data Layer has audited
  Binance USD-M Tier 1 funding-rate history for BTCUSDT and ETHUSDT;
  QuantConnect implementation would require an approved custom-data
  path or separate verification.
- If unavailable: this candidate is blocked until an alternative is
  approved in writing by the user. Do NOT proxy with an unrelated
  series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, or H0006 because it is not spot spread
reclaim, wick-based liquidation proxy, microtrend trailing, or
Bollinger/range mean reversion. It is not H0002 because it does not use
BTC-to-ETH lead-lag. It is not H0005 because it is not a same-symbol
compression breakout. It is not H0007 because it does not trade a
scheduled funding-settlement unwind or bar-only displacement around the
funding clock. It is not H0008 because it does not use premium
compression to identify a crowding unwind; the Data Layer row supports
long continuation after an actual `FUND_EXTREME` event at h+72.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 4
- Probability of clearing pre-fee floor (1-5): 5
- Data availability (1-5): 3
- Simplicity (1-5, higher is simpler): 4
- Total: 16

## 8. Decision

- [x] Promote to hypothesis as `H0009_fund_extreme_cross_symbol_continuation.md`.
- [ ] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0021_fund_extreme_cross_symbol_continuation.md`
      with reason. Never delete.
