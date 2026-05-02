# experiments_log.md

Append-only flat log of every verdict. One line per backtest outcome.

Format:

```
YYYY-MM-DD | Hxxxx | <verdict> | trade_count | sharpe | avg_trade_net | max_dd | notes
```

Seed entries (historical, prior to this repo):

```
???? | H0001 | FAIL | n/a | n/a | ~0 percent pre-fee | n/a | ETH spread reclaim MR, ETHUSDC spot 1m
???? | H0003 | FAIL | n/a | n/a | ~-0.05 percent pre-fee | n/a | SOL liquidation wick, SOLUSD spot 5m
???? | H0004 | FAIL | n/a | n/a | ~-0.01 percent pre-fee | n/a | BTC microtrend trailing, BTCUSDT spot 1m
???? | H0006 | FAIL | n/a | n/a | ~-0.006 percent pre-fee | n/a | BTC BB rejection MR, BTCUSDT spot 5m
```

Rules:

- Append-only. Never edit a prior line.
- One line per verdict, not per iteration.
- `avg_trade_net` is post-fee average trade PnL in percent per trade.
- `notes` is short; link to `obsidian/04_Backtests/BTxxxx_...md` for
  detail.

2026-04-29 | H0002 | FAIL / REJECTED | 132 | -0.774 | -0.098 expectancy | 28.3% | S0001 BT0001_H0002_2026-04-29; Net Profit -14.608%; Win Rate 31%; Total Fees 43.07 USDT; failed falsification criteria 1-6; Monte Carlo not allowed; reject permanently and start new researcher cycle with genuinely new mechanism.
2026-04-29 | H0005 | FAIL / REJECTED | n/a | -6.013 | -0.818 expectancy | 88.9% | Smooth Blue Jellyfish; Net Profit -88.903%; Win Rate 10%; PL Ratio 0.74; Total Orders 3392; Total Fees 79.85; Monte Carlo not allowed; reject permanently, no tuning; processed report: obsidian/04_Backtests/Smooth Blue Jellyfish_H0005_2026-04-29/report.md.
2026-05-01 | H0007 | FAIL / REJECTED | 509 | -5.112 | -0.1602% avg post-fee / -0.0802% pre-fee | 48.9% | Determined Orange Mule; Net Profit -48.692%; Win Rate 32%; PF 0.73; Total Orders 1018; Total Fees 48.32 USDT; failed falsification criteria 2-6; Monte Carlo not allowed; reject permanently, no tuning.
