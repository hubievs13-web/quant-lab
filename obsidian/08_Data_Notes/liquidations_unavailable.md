# Historical liquidations — UNAVAILABLE

Free, reliable historical liquidation data for Binance USD-M Futures is
not available in a form we can depend on for backtesting.

Do NOT:

- Assume a native QC dataset for liquidation history.
- Reconstruct liquidations from price wicks. That is a proxy, not
  ground truth. H0003 (SOL liquidation wick) failed at least partly for
  this reason.
- Scrape real-time liquidation feeds and pretend they are historical.
- Use third-party aggregators whose history is paywalled or undocumented
  without first filing a Phase 2 data-layer proposal and getting
  explicit user approval.

If a hypothesis genuinely depends on liquidation flow, it is blocked in
v1. File it and park it.
