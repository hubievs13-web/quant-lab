---
id: CExxxx
slug: short_slug
created: YYYY-MM-DD
mechanism_class: funding | oi | basis | lead_lag | orderflow | other
symbols: [BTCUSDT, ETHUSDT]
profile: A-Maker | A-Taker | B-Position | B   # candidate profile (`.codex/AGENTS.md` Section 3)
execution_tier: M | T
---

# CExxxx — short_slug

## 1. Mechanism

What structural or microstructural feature of Binance USD-M Futures
creates this edge? Be specific. Do not write "market inefficiency".

## 2. Expected pre-fee edge per trade

- Estimate (percent): ...
- Reasoning from first principles: ...
- Floor for the declared execution tier:
  - Tier T: >= 0.30 percent;
  - Tier M: >= 0.20 percent.
- Quoted Data Layer evidence (path + numeric line):
  - file: `data_layer/reports/...`
  - line: "..."

## 3. Expected trade frequency per day per symbol

- ...

## 4. Expected failure modes

List at least 3. Each must be specific enough to be recognized in a
backtest diagnostic.

## 5. Data required

- Bars: 1m / 5m / etc.
- Derivatives features: funding rate, open interest, basis, ...
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: yes / no /
  partial. If partial, specify.
- If unavailable: this candidate is blocked until an alternative is
  approved in writing by the user. Do NOT proxy with an unrelated
  series.

## 6. Distinct-from-rejected statement

One paragraph showing this is not a cosmetic variation of H0001,
H0003, H0004, or H0006.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5):
- Probability of clearing pre-fee floor (1-5):
- Data availability (1-5):
- Simplicity (1-5, higher is simpler):
- Total: sum.

## 8. Decision

- [ ] Promote to hypothesis as `Hxxxx_<slug>.md`.
- [ ] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CExxxx_<slug>.md`
      with reason. Never delete.
