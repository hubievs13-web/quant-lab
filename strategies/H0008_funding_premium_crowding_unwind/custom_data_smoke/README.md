# H0008 Custom Data Smoke Files

These compact CSV files are for a 3-day QuantConnect technical smoke test only. They are copied from already ingested audited TIER 1 data and are not forward-filled, backfilled, interpolated, or synthesized.

## Date Range

- Start: `2024-02-29T00:00:00Z`
- End: `2024-03-03T00:00:00Z` exclusive
- DL0007 missing timestamps are not inside this range.

The range was selected inside 2024 because both symbols have funding rows and complete premium-index 1m rows. It was not selected by strategy PnL or backtest performance.

## Files

| QC parameter | Local file |
|---|---|
| `H0008_FUNDING_BTCUSDT_URL` | `h0008_funding_BTCUSDT_smoke.csv` |
| `H0008_FUNDING_ETHUSDT_URL` | `h0008_funding_ETHUSDT_smoke.csv` |
| `H0008_PREMIUM_BTCUSDT_URL` | `h0008_premium_BTCUSDT_smoke.csv` |
| `H0008_PREMIUM_ETHUSDT_URL` | `h0008_premium_ETHUSDT_smoke.csv` |

## QuantConnect Use

Upload or host the four CSV files so QuantConnect can read them as remote custom data. Then set the four project parameters above to the corresponding accessible CSV URLs.

For the smoke test, use the same 3-day backtest range:

- `2024-02-29` through `2024-03-03` exclusive.

The smoke test is only for custom-data loading, timestamp parsing, fee/slippage model compatibility, next-bar execution diagnostics, and data-gap diagnostics. It is not a strategy verdict and must not be used as a profitability claim.

## Schemas

Funding:

```text
timestamp_utc,symbol,funding_rate,mark_price_at_funding,source,ingested_at_utc
```

Premium:

```text
timestamp_open_utc,timestamp_close_utc,symbol,open,high,low,close,source,ingested_at_utc
```
