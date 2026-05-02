# Decision: H<xxxx> <slug>

Read-only mirror of hypothesis status. Derived from the canonical
store. Never sets status.

## Status

- `active` | `rejected` | `passed` | `pre_backtest_rejected`
- Derived from path of canonical file (see below).

## Canonical files

- Hypothesis: `obsidian/02_Hypotheses/Hxxxx_<slug>.md`
  or `obsidian/05_Rejected/Hxxxx_<slug>.md`
  or `obsidian/06_Passed/Hxxxx_<slug>.md`.
- Strategy note: `obsidian/03_Strategies/Sxxxx_<slug>.md`.
- Strategy code: `strategies/Hxxxx_<slug>/`.
- Backtest report(s): `obsidian/04_Backtests/BTxxxx_Hxxxx_YYYY-MM-DD/`.
- Lesson (if any): `obsidian/07_Lessons/Lxxxx_<slug>.md`.

## Mechanism (one-paragraph quote)

Quote (verbatim) from the hypothesis note. Do not paraphrase.

## Verdict (verbatim)

Quote from the matching backtest report and from
`experiments_log.md`. Do not paraphrase. Do not soften. Do not
harden.

## Forbidden follow-ups

Quote from the hypothesis or rejected note. If absent, leave blank.

## Distinct-from-rejected reminder

If status is `active`, copy the distinct-from-rejected paragraph
from the hypothesis. If status is `rejected` or
`pre_backtest_rejected`, list the rejection reason code(s).

## Open occurrences (if any)

- QC / Lean errors observed during the active backtest:
  `obsidian/wiki/qc_lean/errors/QCERR-xxxx_<slug>.md`.

## Update rule

- Regenerate this page from the canonical files.
- Never edit it to override the canonical store.
- If the wiki and canonical disagree, the canonical store wins.
