# 02_Fee_Slippage_Model

Default model for Binance USD-M Futures backtests in QuantConnect
(Lean v17685).

## Two execution tiers

A hypothesis must declare in its README which tier it targets. The
auditor rejects strategies that mix tiers without a documented mode
switch.

### Tier T (taker, market orders)

- Per-side fee: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Slippage and impact buffer: 0.10 percent round-trip.
- Total round-trip friction: approximately 0.18 percent.

### Tier M (maker, limit orders with adverse-selection model)

- Per-side fee: 0.02 percent (no rebate assumed).
- Round-trip fee: 0.04 percent.
- Slippage on filled limit: 0.02 percent per side conservative buffer
  (a fill is never assumed to be at the exact limit price).
- Optional taker fallback when the limit is not filled within the
  declared time window: full Tier T friction applies on the fallback
  fill.
- Total round-trip friction (pure maker round-trip): approximately
  0.08 percent.
- An adverse-selection rule is REQUIRED. A limit at price L is treated
  as filled on bar t only if both:
  1. The bar reached the price (low_t <= L for buy, high_t >= L for
     sell).
  2. The next bar moved further adverse to the fill side by at least
     0.05 percent.
  Without rule 2, the backtest is assumed to overstate fills and the
  auditor blocks the strategy.

If a strategy is hybrid (maker entry, taker exit on stop) it must
declare both tiers and account each leg accordingly.

## Funding payments

Not included in the friction numbers above. If a strategy holds through
funding settlement, estimate funding cost separately and document it in
the strategy README and diagnostics.

## Pre-fee edge floor

The required pre-fee average per-trade edge depends on the declared
tier:

- Tier T: pre-fee average trade must be >= 0.30 percent per trade.
- Tier M: pre-fee average trade must be >= 0.20 percent per trade
  (because friction is lower).

These floors replace the prior 0.10 percent figure, which was below the
round-trip friction and therefore mathematically incompatible with a
positive-expectancy strategy after costs.

If a hypothesis cannot justify the relevant floor on mechanism alone,
the researcher and the pre-backtest auditor MUST reject it.

## Fee budget gate

For the declared starting capital and target trade frequency, total
annualized friction must not exceed 25 percent of starting capital:

```
expected_annual_friction
    = trades_per_day * 365 * notional_per_trade * round_trip_friction
notional_per_trade
    = starting_capital * margin_fraction * leverage
```

If `expected_annual_friction / starting_capital > 0.25`, the
hypothesis is structurally incompatible with the chosen profile and
must be rejected, regardless of expected pre-fee edge. The auditor
checks this number explicitly.

## Deviations

If a strategy uses a different fee or slippage assumption, state in
the README:

1. Exact numeric values.
2. Reason (venue promotion, VIP tier, alternative venue, etc.).
3. Evidence (a real exchange link or fee schedule snapshot).

No silent changes. No assumed maker rebates. No assumed VIP tier.
