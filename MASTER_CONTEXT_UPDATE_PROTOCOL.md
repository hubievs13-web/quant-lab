# MASTER_CONTEXT_UPDATE_PROTOCOL

## Purpose

`MASTER_CONTEXT.md` is the compact handoff file for ChatGPT Project continuity.

It must be updated by Codex after every major research-cycle event so the user does not manually rewrite project context.

## When to update MASTER_CONTEXT.md

Codex must update `MASTER_CONTEXT.md` after:

1. A hypothesis is rejected.
2. A hypothesis passes preliminary review.
3. A full backtest verdict is issued.
4. A Monte Carlo audit is completed.
5. A strategy moves to paper trading.
6. A strategy is blocked due to unavailable data, QuantConnect limitations, or execution/modeling issues.
7. A major lesson is added.
8. A new current phase begins.

## What to update

Codex must update only the relevant sections:

1. `Last updated`
2. `Current status`
3. `Current rejected hypotheses`
4. `Current active hypothesis`
5. `Latest result`
6. `Key lessons`
7. `Forbidden follow-ups`
8. `Allowed next directions`

Codex must not paste full logs, screenshots, full source code, full report.md content, or long raw data into `MASTER_CONTEXT.md`.

## Size discipline

`MASTER_CONTEXT.md` must stay compact.

Recommended maximum length:
- 1500–3000 words.

If the file becomes too long:
- keep only the latest active cycle in detail;
- summarize older rejected hypotheses in one-line bullets;
- keep only durable lessons.

## Required update format after rejected hypothesis

When a hypothesis is rejected, Codex must add or update a compact block:

```markdown
## H____ final result

Hypothesis:
H_____

Strategy:
S_____

Backtest:
BT_____

Period:
YYYY-MM-DD to YYYY-MM-DD

Metrics:
- Start Equity:
- End Equity:
- Net Profit:
- Sharpe:
- Drawdown:
- Win Rate:
- Completed trades:
- Total Fees:
- Expectancy:

Verdict:
FAIL / REJECTED

Monte Carlo:
Not run because criteria 1–6 failed.
or
Run result: PASS / FAIL / INCONCLUSIVE.

Failed criteria:
- Trade count:
- Sharpe:
- Net avg trade:
- Drawdown:
- Pre-fee avg:
- WR/PF:
- MC:

Lesson:
[1–2 sentences.]

Forbidden follow-ups:
- Do not tune this hypothesis.
- Do not repeat the same mechanism with different thresholds.
- Do not add filters to rescue this failed result.

Allowed next directions:
- [new mechanism 1]
- [new mechanism 2]

Status:
Closed.