# 00_Hard_Rules

Authoritative rules. Mirrors `.codex/AGENTS.md` section 5. If this file
and AGENTS.md diverge, AGENTS.md wins.

1. NEVER tune parameters after a failed backtest.
2. NEVER claim PASS before Monte Carlo audit.
3. NEVER claim PASS unless every falsification criterion is satisfied.
4. Free parameters per hypothesis <= 3.
5. Fee and slippage model per `02_Fee_Slippage_Model.md`.
6. Pre-fee average trade >= 0.10 percent per trade.
7. No data leakage. See `03_No_Leakage_Checklist.md`.
8. Verdict is PASS / FAIL / INCONCLUSIVE. No "almost passed".
9. No hidden optimization. A parameter change after seeing results =
   a new hypothesis note.
10. No emoji in code or docs.
11. User-facing prose in Russian where natural; code and configs in
    English.
12. Never fabricate data. Mark unavailable data as unavailable.
