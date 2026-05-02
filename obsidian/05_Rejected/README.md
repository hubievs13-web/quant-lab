# 05_Rejected

Permanent graveyard. Two layers:

- `pre_backtest_rejected/` — hypotheses and candidate edges that failed
  pre-backtest manual review or auditor pre-backtest audit. Never made
  it into QuantConnect. The reason is recorded but no live numbers
  exist.
- This folder root — hypotheses that ran a backtest in QuantConnect and
  were rejected by the Devin chat after Falsification Framework V3
  evaluation. Each note has a Post-mortem section appended.

## Hard rules

- Never delete a note. Files are moved here, never removed.
- Never edit the original hypothesis body once a note is in
  `05_Rejected/`. New context is appended in a Post-mortem section.
- Never rename to hide history.
- Codex MUST read this folder (root and `pre_backtest_rejected/`) and
  `07_Lessons/` before proposing a new hypothesis. This reduces the
  risk of repeated ideas but does not guarantee prevention. Every new
  hypothesis must include a distinct-from-rejected section explaining
  why it is not H0001 / H0003 / H0004 / H0006 or a disguised variant.

## Reason codes used in `pre_backtest_rejected/`

- `duplicate_mechanism`            — too close to H0001/H0003/H0004/H0006.
- `too_many_free_parameters`       — more than 3 free parameters.
- `weak_pre_fee_edge_justification`— pre-fee floor not justified a priori.
- `not_futures_specific`           — mechanism would work the same on
                                     spot; defeats v1 purpose.
- `data_unavailable`               — required data is not in QC Lean
                                     v17685 and no Phase 2 data layer
                                     is in scope.
- `leakage_risk`                   — execution model has same-bar or
                                     multi-asset leakage that cannot
                                     be cleanly removed.
- `unclear_execution_model`        — entry/exit rules are ambiguous.
- `other`                          — must be explained in the note body.

## Lifecycle

1. Pre-backtest rejection: file moved to `pre_backtest_rejected/`
   with reason from the list above.
2. Post-backtest rejection: file moved to `05_Rejected/` (root) with
   a Post-mortem section.
3. Files do not move out of `05_Rejected/` afterwards.
