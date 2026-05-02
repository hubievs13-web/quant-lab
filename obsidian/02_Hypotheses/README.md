# 02_Hypotheses

Active hypotheses. One file per hypothesis.

## How to create a new hypothesis

1. Run Codex in researcher mode (see `.codex/README.md`).
2. Codex produces `Hxxxx_<slug>.md` here, using
   `_TEMPLATE_hypothesis.md`.
3. You review the note manually. Check:
   - Distinct-from-rejected statement is honest.
   - Free parameters <= 3.
   - Pre-fee edge floor justified a priori.
   - Data is actually available in QC Lean v17685.
4. If the note fails any of the above, do NOT delete it. Move it to
   `../05_Rejected/pre_backtest_rejected/Hxxxx_<slug>.md` using
   `_TEMPLATE_pre_backtest_rejected.md` and record the reason. Then
   rerun researcher mode with the feedback. Do NOT tweak the note to
   force a pass.

## ID scheme

Zero-padded four-digit numbers. Used IDs to date: H0001, H0003, H0004,
H0006 (all rejected). Next free: H0002, H0005, H0007, H0008, ...

## Lifecycle

- Here while active.
- Moved to `../05_Rejected/` on FAIL.
- Moved to `../06_Passed/` on FINAL PASS.
- Never deleted.
