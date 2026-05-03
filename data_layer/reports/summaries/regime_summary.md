# Regime Summary

Last refresh: 2026-05-03 12:48 UTC.
Source: `data_layer/store/processed/regimes/binance/<SYMBOL>/<TF>.parquet`.
Thresholds: `data_layer/config/regimes.yaml` and `data_layer/process/regimes.py:THRESH`.

## Latest bar

| timeframe | last bar | composite | confidence |
|---|---|---|---|
| 5m | 2026-05-02 23:55 UTC | T=chop|V=mid|F=ID|B=ID|C=balanced|L=normal | 0.667 |
| 1h | 2026-05-02 23:00 UTC | T=up_trend|V=low|F=ID|B=ID|C=balanced|L=normal | 0.667 |

## Distribution (5m, 2016 bars)

| component | label | count | share |
|---|---|---|---|
| Trend | up_trend | 17 | 0.8% |
| Trend | chop | 1874 | 93.0% |
| Trend | down_trend | 78 | 3.9% |
| Trend | insufficient_data | 47 | 2.3% |
| Vol | low | 461 | 22.9% |
| Vol | mid | 234 | 11.6% |
| Vol | high | 290 | 14.4% |
| Vol | insufficient_data | 1031 | 51.1% |
| Funding | flat | 1441 | 71.5% |
| Funding | insufficient_data | 575 | 28.5% |
| Basis | insufficient_data | 2016 | 100.0% |
| Crowding | balanced | 2015 | 100.0% |
| Crowding | insufficient_data | 1 | 0.0% |
| Liquidity | thin | 108 | 5.4% |
| Liquidity | normal | 1612 | 80.0% |
| Liquidity | thick | 273 | 13.5% |
| Liquidity | insufficient_data | 23 | 1.1% |

## Distribution (1h, 720 bars)

| component | label | count | share |
|---|---|---|---|
| Trend | up_trend | 236 | 32.8% |
| Trend | chop | 340 | 47.2% |
| Trend | down_trend | 97 | 13.5% |
| Trend | insufficient_data | 47 | 6.5% |
| Vol | low | 233 | 32.4% |
| Vol | mid | 166 | 23.1% |
| Vol | high | 214 | 29.7% |
| Vol | insufficient_data | 107 | 14.9% |
| Funding | flat | 618 | 85.8% |
| Funding | neg_extreme | 55 | 7.6% |
| Funding | insufficient_data | 47 | 6.5% |
| Basis | insufficient_data | 720 | 100.0% |
| Crowding | balanced | 167 | 23.2% |
| Crowding | insufficient_data | 553 | 76.8% |
| Liquidity | thin | 35 | 4.9% |
| Liquidity | normal | 563 | 78.2% |
| Liquidity | thick | 99 | 13.8% |
| Liquidity | insufficient_data | 23 | 3.2% |

## Notes

- `basis_regime` is `insufficient_data` everywhere in Phase 2/3 (no mark/index series ingested yet).
- `crowding_regime` is `balanced` whenever `top_trader_position_ratio` is present; richer crowded_long / crowded_short labels are Phase 4.
- 5m `funding_regime` insufficient bars (~last 2 days) reflect missing May-2026 monthly funding zip; arrives once month rolls.
