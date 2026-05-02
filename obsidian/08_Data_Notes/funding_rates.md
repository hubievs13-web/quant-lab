# Funding rates — availability and use

## What funding rate is

An 8-hour periodic payment between longs and shorts on Binance USD-M
Futures perpetuals, derived from a premium index plus an interest-rate
component, capped. Positive funding: longs pay shorts. Negative funding:
shorts pay longs.

## Why it matters for an edge hypothesis

- Persistently positive funding can signal crowded long positioning.
- Persistently negative funding can signal crowded short positioning.
- Funding extremes have historically coincided with mean-reverting
  setups at various horizons, but the effect size and stability at
  intraday 1m to 5m on BTCUSDT / ETHUSDT are NOT guaranteed and must be
  justified per hypothesis.

## Availability in QuantConnect Lean v17685

- Bar data (minute) for BTCUSDT and ETHUSDT perpetuals: expected to be
  available via the Crypto Futures dataset. Confirm in QC documentation
  at the time of implementation.
- Historical 8-hour funding rate series as a native QC dataset: NOT
  confirmed. If a hypothesis requires funding as an input feature, the
  engineer must verify dataset availability before writing code. If not
  available, do NOT fabricate or proxy. File the hypothesis as blocked
  and propose a Phase 2 data layer.
- Live funding rate during a QC backtest: not used in v1.

## What we do NOT assume

- That funding history is freely available at minute resolution in QC
  for BTCUSDT and ETHUSDT. It is typically 8-hourly at source.
- That funding forecasts can be synthesized from price alone. They
  cannot, reliably.

## If blocked

If a funding-dependent hypothesis is blocked by QC data gaps, options
are:

1. Choose a different mechanism that works with bar data only.
2. Propose a Phase 2 local data layer (CSV / Parquet / DuckDB) ingesting
   Binance's public API. That is a separate project phase.
