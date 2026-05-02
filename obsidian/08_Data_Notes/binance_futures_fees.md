# Binance USD-M Futures — fees and margin assumptions (v1)

## Fees used in backtests

- Taker fee per side: 0.04 percent.
- Round-trip fee: 0.08 percent.
- Slippage + impact buffer: additional approximately 0.10 percent on a
  round-trip basis so total round-trip friction is approximately 0.18
  percent.

## Real Binance Futures retail fees (reference)

Retail tier on Binance USD-M Futures has been approximately 0.02 / 0.05
percent (maker / taker) for regular users without BNB discount and
without VIP tier. With BNB fee discount and VIP tiers, both drop. For
v1 we do NOT assume any discount. We assume 0.04 percent taker per side
as a conservative round number that sits between promotional and
standard retail pricing. If the hypothesis requires a different
assumption, state it explicitly with evidence.

## Margin

- Isolated margin only in v1.
- Leverage 2x to 3x maximum.
- Starting capital USD 200 (real target). Backtest starting cash
  in QC can be set accordingly but should not be tuned to flatter the
  numbers.

## Funding

- Funding is settled every 8 hours on Binance USD-M Futures.
- If the strategy's average holding time is less than 8 hours and
  positions rarely span funding settlements, funding cost is usually
  small but not zero. If positions routinely cross funding settlement,
  include an explicit funding cost estimate in the strategy README.
