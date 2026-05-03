# Regime Summary

Last refresh: 2026-05-03 13:39 UTC.
Source: `data_layer/store/processed/regimes/binance/<SYMBOL>/<TF>.parquet`.
Thresholds: `data_layer/config/regimes.yaml` and `data_layer/process/regimes.py:THRESH`.

## Latest bar

| timeframe | last bar | composite | confidence |
|---|---|---|---|
| 5m | 2026-05-02 23:55 UTC | T=chop|V=mid|F=ID|B=neutral|C=balanced|L=normal | 0.833 |
| 1h | 2026-05-02 23:00 UTC | T=up_trend|V=low|F=ID|B=neutral|C=balanced|L=normal | 0.833 |

## Distribution (5m, 25920 bars)

| component | label | count | share |
|---|---|---|---|
| Trend | up_trend | 1572 | 6.1% |
| Trend | chop | 22695 | 87.6% |
| Trend | down_trend | 1606 | 6.2% |
| Trend | insufficient_data | 47 | 0.2% |
| Vol | low | 9505 | 36.7% |
| Vol | mid | 7760 | 29.9% |
| Vol | high | 7624 | 29.4% |
| Vol | insufficient_data | 1031 | 4.0% |
| Funding | pos_extreme | 192 | 0.7% |
| Funding | flat | 24386 | 94.1% |
| Funding | neg_normal | 287 | 1.1% |
| Funding | neg_extreme | 480 | 1.9% |
| Funding | insufficient_data | 575 | 2.2% |
| Basis | neutral | 14644 | 56.5% |
| Basis | discount_rich | 11276 | 43.5% |
| Crowding | balanced | 8639 | 33.3% |
| Crowding | insufficient_data | 17281 | 66.7% |
| Liquidity | thin | 1849 | 7.1% |
| Liquidity | normal | 20537 | 79.2% |
| Liquidity | thick | 3511 | 13.5% |
| Liquidity | insufficient_data | 23 | 0.1% |

## Distribution (1h, 4320 bars)

| component | label | count | share |
|---|---|---|---|
| Trend | up_trend | 1013 | 23.4% |
| Trend | chop | 2090 | 48.4% |
| Trend | down_trend | 1170 | 27.1% |
| Trend | insufficient_data | 47 | 1.1% |
| Vol | low | 1524 | 35.3% |
| Vol | mid | 1201 | 27.8% |
| Vol | high | 1488 | 34.4% |
| Vol | insufficient_data | 107 | 2.5% |
| Funding | pos_extreme | 39 | 0.9% |
| Funding | pos_normal | 144 | 3.3% |
| Funding | flat | 3912 | 90.6% |
| Funding | neg_extreme | 178 | 4.1% |
| Funding | insufficient_data | 47 | 1.1% |
| Basis | neutral | 2972 | 68.8% |
| Basis | discount_rich | 1348 | 31.2% |
| Crowding | balanced | 719 | 16.6% |
| Crowding | insufficient_data | 3601 | 83.4% |
| Liquidity | thin | 221 | 5.1% |
| Liquidity | normal | 3433 | 79.5% |
| Liquidity | thick | 643 | 14.9% |
| Liquidity | insufficient_data | 23 | 0.5% |

## Notes

- `basis_regime` now uses real mark/index ingest from data.binance.vision; `discount_rich` flags index > mark by enough bp.
- `crowding_regime` is `balanced` whenever `top_trader_position_ratio` is present; richer crowded_long / crowded_short labels still pending.
- Residual `insufficient_data` in `funding_regime` reflects the tail of the window where the next monthly funding zip is not yet on the CDN.
