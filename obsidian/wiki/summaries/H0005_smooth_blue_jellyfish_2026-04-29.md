# Summary: H0005 Smooth Blue Jellyfish backtest 2026-04-29

Compact processed knowledge note. Read this instead of opening the
backtest folder directly. Folder contains a 2.9 MB `statistics.json`
that LOW TOKEN MODE forbids by default.

## Sources

- `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/report.md` (3.2 KB)
- `experiments_log.md` line 29 (verdict)

## Status

- ingested-at: 2026-05-02
- last-updated: 2026-05-02
- supersedes: none

## Key facts

- Hypothesis: H0005 `perp_compression_breakout` (orderflow, 5m).
- Strategy: S0005 / `strategies/H0005_perp_compression_breakout/`.
- QC project 30774195, Lean v17685.
- Symbols: BTCUSDT, ETHUSDT.
- Windows: in-sample 2024-01-01; out-of-sample 2024-01-01 to 2025-01-01.
- Final external Devin verdict: FAIL / REJECTED. Monte Carlo not
  allowed.

## Numbers

| metric | value | source |
|---|---|---|
| total_trades (orders) | 1696 (3392 orders) | report.md Section 3; verdict line |
| net_return | -88.903% | report.md Section 3 |
| sharpe | -6.013 | report.md Section 3 |
| max_drawdown_run | -36.79% (verdict line says 88.9%) | report.md Section 3 |
| win_rate | 10% | report.md Section 3 |
| profit_factor | 0.1732 | report.md Section 3 |
| pl_ratio | 0.74 | verdict line |
| total_fees | 79.85 USDT | verdict line |
| expectancy | -0.818 | verdict line |

## Failed criteria

- Sharpe -6.013 < 1.0; net return -88.903%; WR 10%; PF 0.1732;
  fees alone (79.85 USDT) > 39% of starting equity; drawdown
  catastrophic. Trade count was the only criterion satisfied.

## Caveats

- Confidence: HIGH (primary artifacts present).
- Folder is missing canonical `trades.csv` and `orders.csv` per
  `obsidian/00_LINT_REPORT.md` Section 5.
- Folder name uses raw QuantConnect export name
  `Smooth Blue Jellyfish_H0005_2026-04-29` instead of canonical
  `BTxxxx_H0005_2026-04-29` pattern. Rename deferred per
  `00_LINT_REPORT.md`.
- `statistics.json` is 2.9 MB; do not read.

## Cross-links

- Decision: `obsidian/wiki/decisions/decisions_index.md` (H0005 row).
- Hypothesis (rejected): `obsidian/05_Rejected/H0005_perp_compression_breakout.md`.
- Backtest folder: `obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/`.

## Verdict touch

- Does not modify any verdict.
- Verbatim verdict from `experiments_log.md` line 29:
  `2026-04-29 | H0005 | FAIL / REJECTED | n/a | -6.013 | -0.818 expectancy | 88.9% | Smooth Blue Jellyfish; Net Profit -88.903%; Win Rate 10%; PL Ratio 0.74; Total Orders 3392; Total Fees 79.85; Monte Carlo not allowed; reject permanently, no tuning; processed report: obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/report.md.`
