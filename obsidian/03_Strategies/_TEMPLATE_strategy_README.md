---
id: Sxxxx
hypothesis: Hxxxx
slug: short_slug
created: YYYY-MM-DD
status: draft   # draft | ready_for_qc | submitted | verdict_pending | closed
---

# Sxxxx — short_slug (implements Hxxxx)

## 1. Link to hypothesis

`obsidian/02_Hypotheses/Hxxxx_<slug>.md`

## 2. Mechanism summary

Three sentences max. Copy from hypothesis note.

## 3. Free parameters (<= 3)

| Name | Value | Role | Justification |
|------|-------|------|---------------|
| ...  | ...   | ...  | ...           |

## 4. Fee and slippage assumptions

- Taker fee per side: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Total round-trip friction assumption: ~0.18 percent.
- Funding: [included / excluded]. If included, method.

Any deviation from `obsidian/01_Rules/02_Fee_Slippage_Model.md` must be
stated here with numbers and justification.

## 5. Execution model

- Signal bar to execution bar relationship.
- Order type.
- Multi-asset alignment rule if any.

## 6. Expected trade count

- Per day per symbol: ...
- Per OOS window: ...

## 7. Diagnostics plan

See `diagnostics.md`.

## 8. Known risks and expected failure modes

- ...

## 9. Brokerage model verification step

QuantConnect Lean v17685 exposes brokerage models for Binance. Names and
exact symbol mapping for USD-M Futures perpetuals may change between
Lean versions. Before the first full backtest, the user must:

1. Open QuantConnect project 30774195.
2. Paste `main.py`.
3. Run with a 3-day window and confirm:
   - Fills happen on BTCUSDT (and ETHUSDT if used).
   - No "brokerage model does not support symbol" warnings.
   - Leverage is reported as 2x or 3x as configured.
4. If any of the above fails, do NOT proceed to the full backtest.
   Update this note with the observed behavior and either fix the
   brokerage-model code or mark the hypothesis as blocked.

## 10. Paste-ready code

See `strategies/Hxxxx_<slug>/main.py`.
