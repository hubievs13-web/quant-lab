# Post-mortem (appended to rejected hypothesis note)

Never edit the original hypothesis body. Append this section at the very
end of `Hxxxx_<slug>.md` after it is moved to `05_Rejected/`.

---

## Post-mortem

- Date of verdict: YYYY-MM-DD.
- Backtest report: `../04_Backtests/BTxxxx_Hxxxx_YYYY-MM-DD.md`.
- Failed criteria (from framework V3): ...
- Observed metrics:
  - trade_count: ...
  - sharpe_oos: ...
  - avg_trade_net: ...
  - avg_trade_pre_fee: ...
  - max_dd: ...
  - win_rate: ...
  - profit_factor: ...
- Which a-priori assumption from the hypothesis turned out wrong?
- Generalizable lesson (if any). If yes, create
  `../07_Lessons/Lxxxx_<slug>.md` and link here.
- Related rejected IDs (if this failure pattern echoes a previous one):

## What is NOT allowed here

- Re-running the same mechanism with different parameters. That is
  tuning. File a new hypothesis under `../02_Hypotheses/` with a
  genuinely different mechanism.
- Editing the original hypothesis content above to look smarter in
  hindsight.
