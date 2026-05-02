# Pre-backtest rejection record (appended to the moved note)

Used when a hypothesis or candidate edge is rejected BEFORE running a
backtest in QuantConnect. The original note body is preserved
unchanged. Append this section at the very end after moving the file
to `obsidian/05_Rejected/pre_backtest_rejected/`.

---

## Pre-backtest rejection

- Date of rejection: YYYY-MM-DD.
- Source: researcher_self_review | manual_user_review | auditor_pre_backtest_audit
- Reason code (one of):
  - duplicate_mechanism
  - too_many_free_parameters
  - weak_pre_fee_edge_justification
  - not_futures_specific
  - data_unavailable
  - leakage_risk
  - unclear_execution_model
  - other
- Reason detail: one paragraph. Be specific. Name which rejected
  hypothesis it duplicates, or which parameter pushed the count over 3,
  or which data field is missing in QC Lean v17685, etc.
- Auditor checklist excerpt (only if rejected at audit time): paste the
  failed items.
- Related rejected IDs (if duplicate_mechanism): H0001 / H0003 / H0004
  / H0006 / other.
- Lesson candidate: yes/no. If yes, link the new
  `obsidian/07_Lessons/Lxxxx_<slug>.md` here.

## What is NOT allowed here

- Editing the original note body above to look better in hindsight.
- Re-filing the same idea under a new ID with one parameter changed.
  That is tuning. A new hypothesis requires a different mechanism.
- Deleting this file later. It is a permanent record.
