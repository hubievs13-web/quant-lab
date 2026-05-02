# 02_Fee_Slippage_Model

Default model for Binance USD-M Futures backtests in QuantConnect
(Lean v17685).

## Fees

- Taker fee: 0.04 percent per side.
- Round-trip fee: 0.08 percent.
- No maker-rebate assumptions in v1. Treat everything as taker.

## Slippage and market impact

- Additional slippage and impact buffer so that total round-trip
  friction assumption is approximately 0.18 percent. This is ~0.10
  percent on top of pure fees, which is a conservative buffer for:
  - bid-ask half-spread on BTC/ETH perpetuals (small but non-zero on
    1m bars),
  - market order walk-through on small size (USD 200 capital is tiny
    so walk-through is negligible, but the buffer absorbs latency and
    quote-staleness),
  - funding payments are NOT included here. If a strategy holds
    through funding settlement, estimate funding cost separately.

## Pre-fee edge floor

- Expected pre-fee average trade must be >= 0.10 percent per trade.
- If a hypothesis cannot justify this floor on mechanism alone, reject
  it at the researcher stage.

## Deviations

If a strategy uses a different fee or slippage assumption, state:

1. Exact numeric values.
2. Reason (venue promotion, maker-only execution, etc.).
3. Evidence.

No silent changes.
