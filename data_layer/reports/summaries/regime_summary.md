# Regime Summary

Last refresh: 2026-05-03 13:12 UTC.
Source: `data_layer/store/processed/regimes/binance/<SYMBOL>/<TF>.parquet`.
Thresholds: `data_layer/config/regimes.yaml` and `data_layer/process/regimes.py:THRESH`.

## Latest bar

| timeframe | last bar | composite | confidence |
|---|---|---|---|
| 5m | 2026-05-02 23:55 UTC | T=chop|V=mid|F=ID|B=neutral|C=balanced|L=normal | 0.833 |
| 1h | 2026-05-02 23:00 UTC | T=up_trend|V=low|F=ID|B=neutral|C=balanced|L=normal | 0.833 |

## Distribution (5m, 8640 bars)

| component | label | count | share |
|---|---|---|---|
| Trend | up_trend | 338 | 3.9% |
| Trend | chop | 8090 | 93.6% |
| Trend | down_trend | 165 | 1.9% |
| Trend | insufficient_data | 47 | 0.5% |
| Vol | low | 2520 | 29.2% |
| Vol | mid | 2567 | 29.7% |
| Vol | high | 2522 | 29.2% |
| Vol | insufficient_data | 1031 | 11.9% |
| Funding | flat | 7394 | 85.6% |
| Funding | neg_extreme | 671 | 7.8% |
| Funding | insufficient_data | 575 | 6.7% |
| Basis | neutral | 4479 | 51.8% |
| Basis | discount_rich | 4161 | 48.2% |
| Crowding | balanced | 8639 | 100.0% |
| Crowding | insufficient_data | 1 | 0.0% |
| Liquidity | thin | 524 | 6.1% |
| Liquidity | normal | 6946 | 80.4% |
| Liquidity | thick | 1147 | 13.3% |
| Liquidity | insufficient_data | 23 | 0.3% |

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
