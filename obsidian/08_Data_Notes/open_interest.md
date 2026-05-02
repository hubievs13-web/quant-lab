# Open interest — availability and use

## What OI is

Total notional (or coin) of outstanding perpetual positions on a venue
at a given point in time. Changes in OI combined with price moves are
commonly used to classify flow (new longs, short covering, etc.).

## Why it might matter

- Sharp OI increase with price up can indicate fresh long flow; OI
  decrease with price up can indicate short covering.
- At intraday horizons on BTCUSDT / ETHUSDT, an edge hypothesis using
  OI must specify the time resolution (typically 5m or 1h at source)
  and alignment to bar timestamps to avoid leakage.

## Availability in QuantConnect Lean v17685

- Native OI history as a QC dataset for Binance USD-M Futures: NOT
  confirmed.
- If required by a hypothesis, the engineer must verify dataset
  availability. If not available, treat as blocked and do not proxy.

## Alignment rules (when OI is eventually available)

- Use the OI value strictly before the signal bar's open to form a
  signal that executes at or after the signal bar's close (or next bar
  open per AGENTS.md section 5 rule 7).
- Do not use OI snapshots whose timestamp is the same as or later than
  the execution bar.
