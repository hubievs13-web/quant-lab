---
id: BTxxxx
hypothesis: Hxxxx
strategy: Sxxxx
date: YYYY-MM-DD
qc_project_id: 30774195
lean_version: v17685
window_is: [YYYY-MM-DD, YYYY-MM-DD]
window_oos: [YYYY-MM-DD, YYYY-MM-DD]
evidence_confidence: OK   # OK | LOW_CONFIDENCE | NO_EVIDENCE
verdict_draft: READY_FOR_DEVIN_REVIEW   # FAIL_DRAFT | INCONCLUSIVE_DRAFT | READY_FOR_DEVIN_REVIEW
verdict: pending   # pending | FAIL | INCONCLUSIVE | PRELIMINARY_PASS | FINAL_PASS  (set by Devin chat only)
---

# BTxxxx — Hxxxx run YYYY-MM-DD

## 1. Run context

- Hypothesis: `obsidian/02_Hypotheses/Hxxxx_<slug>.md`
- Strategy: `strategies/Hxxxx_<slug>/`
- QC backtest URL / name: ...
- Start / end: ...
- Starting capital: USD 200.
- Leverage used: ...
- Fee model in effect: taker 0.04 percent per side, round-trip friction
  ~0.18 percent. Any deviation noted explicitly.

## 2. QuantConnect overview metrics

Paste the Overview panel numbers verbatim.

- Net profit: ...
- Sharpe (annualized): ...
- Trade count: ...
- Win rate: ...
- Profit factor: ...
- Payoff ratio: ...
- Max drawdown: ...
- Average trade: ...  (post-fee)

Screenshots:

- overview.png
- equity_curve.png

## 3. In-sample vs out-of-sample split

- IS window: ...
- OOS window: ...
- Numbers for each window separately (copy the same fields as above).

## 4. Pre-fee vs post-fee average trade

- Post-fee avg trade: ... (from QC)
- Pre-fee avg trade: ... (reconstructed by adding back 0.08 percent
  round-trip fee plus 0.10 percent slippage buffer, per trade)
- Pre-fee floor (>= 0.10 percent) satisfied: yes/no.

## 5. Evidence inventory and confidence

Machine-readable evidence is PRIMARY. Screenshots and PDFs are
SECONDARY.

Primary (must be present for a high-confidence verdict):

- [ ] trades.csv
- [ ] orders.csv
- [ ] logs.txt
- [ ] statistics.txt or statistics.json

Secondary (helpful but not sufficient on their own):

- [ ] overview.png
- [ ] equity_curve.png
- [ ] report.pdf

If only secondary is present, set `evidence_confidence: LOW_CONFIDENCE`
in the front matter and request the missing primary files before the
Devin chat issues anything beyond INCONCLUSIVE.

## 5b. Trades log

Attach orders.csv or paste summary here. Include at least:

- total_trades
- long_trades / short_trades
- avg_holding_bars
- trades_per_day

## 6. Diagnostic logs

Paste relevant lines from QC Debug log. Look for:

- signal-bar vs execution-bar timestamps (no leakage).
- brokerage-model warnings.
- data-gap warnings.
- daily summaries emitted by `main.py`.

## 7. Framework check (criteria 1 to 6)

| # | Criterion                                 | Observed | Pass |
|---|-------------------------------------------|----------|------|
| 1 | Trade count >= 300 (intraday)             |          |      |
| 2 | OOS Sharpe > 1.0                          |          |      |
| 3 | OOS net avg trade > 0                     |          |      |
| 4 | Max drawdown < 25 percent                 |          |      |
| 5 | Pre-fee avg trade >= 0.10 percent         |          |      |
| 6 | WR >= 50 percent IS and OOS, OR PF >= 1.25|          |      |

## 8. Preliminary verdict draft (filled by user / script, not Devin)

- verdict_draft: FAIL_DRAFT / INCONCLUSIVE_DRAFT / READY_FOR_DEVIN_REVIEW
- reason: ...

## 8b. Preliminary verdict (filled by Devin chat only)

- verdict: FAIL / INCONCLUSIVE / PRELIMINARY_PASS
- reason: ...

## 9. Monte Carlo (only if PRELIMINARY_PASS)

- input: per-trade PnL CSV path.
- simulations: 1000+.
- P5 final equity: ...
- Pass: yes/no.

## 10. Final verdict (filled by Devin chat)

- verdict: FAIL / INCONCLUSIVE / PRELIMINARY_PASS / FINAL_PASS
- summary reasoning: ...

## 11. Follow-up

- If FAIL: auditor moves Hxxxx to `05_Rejected/` and adds post-mortem.
- If INCONCLUSIVE: note what evidence is needed; do NOT tune.
- If PRELIMINARY_PASS: schedule Monte Carlo.
- If FINAL_PASS: move Hxxxx to `06_Passed/` and plan paper trading.
