# results/

Machine-readable mirror of QuantConnect runs and their outcomes.

## Layout

```
results/
  README.md
  experiments.csv      # one row per backtest run (upsert by backtest_id)
  raw/                 # user drops raw QC export bundles here, one folder per run
  trades/              # extracted trades CSVs (if you split them out)
  orders/              # extracted orders CSVs
  logs/                # extracted logs.txt
  reports/             # extracted statistics / report.pdf copies
```

The canonical Obsidian-side report is in
`obsidian/04_Backtests/<BTID>_<HID>_<DATE>/report.md`. The CSV here is
the structured shadow of that note.

## experiments.csv

Header (do not edit; columns must match
`scripts/process_qc_backtest.py`):

```
hypothesis_id,strategy_id,backtest_id,date,symbols,timeframe,
is_start,is_end,oos_start,oos_end,total_trades,net_return,sharpe,
max_drawdown,win_rate,profit_factor,avg_trade_net,avg_trade_prefee,
mc_p5_final_equity,mc_p95_max_drawdown,mc_prob_loss,
evidence_confidence,verdict,reason,artifacts_path
```

Notes on key columns:

- `mc_p95_max_drawdown` is the 95th percentile of simulated max
  drawdown (high percentile = worse path), in percent. PASS requires
  this < 25.
- `evidence_confidence` is one of `OK`, `LOW_CONFIDENCE`,
  `NO_EVIDENCE`. Set by `process_qc_backtest.py` based on which
  artifacts were present in `results/raw/<run>/`.

Empty cells mean UNKNOWN / not yet filled. The script never invents
values. `verdict` here is a draft (FAIL_DRAFT / INCONCLUSIVE_DRAFT /
READY_FOR_DEVIN_REVIEW) until the Devin chat replaces it.

## How to add a run

1. Place exported QC files in `results/raw/BT<ID>_H<ID>_<DATE>/`. Files
   the script knows: `overview.png`, `equity_curve.png`, `trades.csv`,
   `orders.csv`, `logs.txt`, `report.pdf`, `statistics.txt`,
   `statistics.json`. Anything else is copied through as-is.
2. Run:
   ```
   python scripts/process_qc_backtest.py \
       --hypothesis H0007 --strategy S0007 \
       --raw-dir results/raw/BT0007_H0007_2026-04-29 \
       --symbols BTCUSDT,ETHUSDT --timeframe 1m \
       --is-window 2024-01-01:2024-12-31 \
       --oos-window 2025-01-01:2025-12-31
   ```
3. The script copies artifacts into
   `obsidian/04_Backtests/BT0007_H0007_2026-04-29/`, writes
   `report.md`, and appends/upserts a row in `experiments.csv`.
4. Send `report.md` and the primary CSVs / logs to the Devin chat.
