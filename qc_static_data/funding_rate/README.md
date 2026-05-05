# Funding-rate CSVs for QuantConnect custom data

These two CSVs flatten the audited Binance USD-M funding history from
`data_layer/store/raw/binance/funding/{BTCUSDT,ETHUSDT}/*.parquet`
(gitignored under `data_layer/store/`) into the on-disk schema that the
H0009 strategy (and any other QC strategy that needs raw funding
observations) reads as `PythonData`:

```text
timestamp_utc,symbol,funding_rate,funding_interval_ms
2023-05-01T00:00:00Z,BTCUSDT,2.435e-05,28800000
...
```

- One row per funding settlement (Binance USD-M settles every 8 hours).
- `timestamp_utc` is ISO 8601 with a `Z` suffix.
- `funding_rate` is the realised settlement rate, NOT the predicted rate.
- Range: 2023-05-01 .. 2026-04-30 (3 years), 3288 rows per symbol.
- These files are ~155 KB each, gitignored by no rule, and intended to
  be served as-is from `raw.githubusercontent.com` to QC at backtest
  time.

## Re-generating

If the underlying funding parquet files are extended (e.g. you ingest
new months from Binance Vision), re-run the concatenation script:

```python
import pandas as pd
from pathlib import Path

OUT_DIR = Path("data_layer/store/raw/binance/funding_csv_for_qc")
for symbol in ["BTCUSDT", "ETHUSDT"]:
    src = Path(f"data_layer/store/raw/binance/funding/{symbol}")
    files = sorted(src.glob(f"{symbol}-fundingRate-*.parquet"))
    df = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
    df = df.sort_values("ts_settle_ms").drop_duplicates("ts_settle_ms")
    df["timestamp_utc"] = pd.to_datetime(df["ts_settle_ms"], unit="ms", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df[["timestamp_utc", "symbol", "funding_rate", "funding_interval_ms"]] \
        .to_csv(OUT_DIR / f"{symbol}_funding_rate.csv", index=False, lineterminator="\n")
```

## Use in QuantConnect

Set the following project parameters on QC project 30774195 (or any QC
project that paste-runs an H-series strategy needing funding):

| QC parameter | Raw URL |
|---|---|
| `H0009_FUNDING_BTCUSDT_URL` | `https://raw.githubusercontent.com/hubievs13-web/quant-lab/main/qc_static_data/funding_rate/BTCUSDT_funding_rate.csv` |
| `H0009_FUNDING_ETHUSDT_URL` | `https://raw.githubusercontent.com/hubievs13-web/quant-lab/main/qc_static_data/funding_rate/ETHUSDT_funding_rate.csv` |

The repo is public, so QC's HTTP fetch will succeed without auth. If the
repo is ever made private, replace `raw.githubusercontent.com/<…>/main/`
with a signed URL or move the CSVs to a public S3 bucket / gist.
