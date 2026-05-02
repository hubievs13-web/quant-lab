---
id: CE0009
slug: perp_compression_breakout
created: 2026-04-29
mechanism_class: orderflow
symbols: [BTCUSDT, ETHUSDT]
---

# CE0009 - perp_compression_breakout

## 1. Mechanism

In Binance USD-M perpetuals, tight realized range after active trading can reflect temporary leverage balance and clustered stop/market orders around the compression range. When a completed 5m bar breaks out of that compressed range, forced short-horizon futures flow can extend the move for the next few bars. The edge is a futures order-flow expansion after compression, not cross-asset lead-lag and not a same-symbol microtrend count.

## 2. Expected pre-fee edge per trade

- Estimate (percent): 0.12 to 0.20 percent.
- Reasoning from first principles: the setup avoids ordinary continuation and only enters after a completed low-range compression resolves through a prior range boundary. The expected raw move must exceed the 0.18 percent round-trip friction after testing; a priori, stop and market-order clustering around a compressed futures range can produce a short burst above the 0.10 percent pre-fee floor.

## 3. Expected trade frequency per day per symbol

- Approximately 3 to 7 trades per day per symbol.
- Across BTCUSDT and ETHUSDT combined, approximately 6 to 14 trades per day before overlaps or missing data.

## 4. Expected failure modes

- Compression range breaks are false breaks and immediately revert inside the range.
- The compression definition selects quiet periods with too little follow-through.
- Breakout extension exists but average move is below the 0.18 percent round-trip friction model.
- BTCUSDT and ETHUSDT produce clustered simultaneous signals and over-concentrate risk.
- QC futures bars are available but fill/slippage modeling makes market entries materially worse than expected.

## 5. Data required

- Bars: 5m Binance USD-M Futures bars for BTCUSDT and ETHUSDT.
- Derivatives features: none beyond futures OHLCV bars. Volume is not required.
- Availability in QC Lean v17685 for BTCUSDT and ETHUSDT: yes / expected for price bars, with verification required. Local notes say minute bars are expected via the Crypto Futures dataset, and current QuantConnect documentation lists Binance Crypto Future price data and `add_crypto_future` support for BTCUSDT/ETHUSDT. Exact project symbol mapping must still be verified before a full backtest.
- If unavailable: this candidate is blocked until an alternative is approved in writing by the user. Do NOT proxy with an unrelated series.

## 6. Distinct-from-rejected statement

This is not H0001, H0003, H0004, H0006, or H0002. It does not fade spot spread/band/wick events, does not use liquidation proxies, does not count consecutive same-symbol microtrend bars, and does not use BTC-to-ETH lead-lag. The mechanism is futures range compression resolving into a same-symbol perpetual breakout, with the compression state as the required futures order-flow setup.

## 7. Preliminary ranking

- Plausibility of mechanism (1-5): 3
- Probability of clearing pre-fee floor (1-5): 3
- Data availability (1-5): 4
- Simplicity (1-5, higher is simpler): 4
- Total: 14

## 8. Decision

- [x] Promote to hypothesis as `H0005_perp_compression_breakout.md`.
- [ ] Park as candidate edge here.
- [ ] Move to `../05_Rejected/pre_backtest_rejected/CE0009_perp_compression_breakout.md`
      with reason. Never delete.
