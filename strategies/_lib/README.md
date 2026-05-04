# strategies/_lib/

Canonical reference implementations of the plumbing every Codex
generated QuantConnect strategy needs:

- fee models (Tier T taker, Tier M maker),
- slippage models (Tier T),
- maker fill proxy with adverse-selection rule (Tier M),
- risk controls (drawdown stop),
- diagnostics (per-trade logger, daily summary).

## Why this exists

QuantConnect's web IDE accepts only a single file (`main.py`). For
that reason, `_lib/` is NOT imported at runtime in QuantConnect. Its
purpose is:

1. Provide a single, tested source of truth for fee, slippage,
   maker-fill, risk, and diagnostic code so engineer-mode does not
   reinvent (and rebreak) plumbing on every hypothesis.
2. Be inlined byte-for-byte into the generated `main.py` by the
   engineer, with class renaming if needed.
3. Be unit-testable offline against the mock in
   `tests/mocks/AlgorithmImports.py` so we know the canonical
   snippet works before it is inlined.
4. Be lintable: `scripts/lint_strategy.py` checks that a generated
   `main.py` contains the expected canonical fee / slippage /
   maker-fill model markers for its declared tier.

## Modules

- `fee_models.py` — `BinanceUMTakerFeeModel`,
  `BinanceUMMakerFeeModel`. Apply per-side fees consistent with
  `obsidian/01_Rules/02_Fee_Slippage_Model.md`.
- `slippage_models.py` — `BinanceUMTakerSlippageModel`. Adds the
  Tier T slippage buffer.
- `maker_fill_proxy.py` — `BinanceUMMakerFillModel`. Implements the
  adverse-selection fill rule for Tier M strategies.
- `risk_controls.py` — `DrawdownStop`. Tracks session peak equity
  and signals a hard stop at 20 percent drawdown.
- `diagnostics.py` — `PerTradeLogger`, `DailySummary`. Standard
  log lines the auditor expects.

## How engineer mode uses _lib

For each `main.py`:

1. Inline the relevant fee model class (Tier T or Tier M) from
   `fee_models.py`.
2. Inline `BinanceUMTakerSlippageModel` (Tier T) or
   `BinanceUMMakerFillModel` (Tier M).
3. Inline `DrawdownStop`.
4. Inline `PerTradeLogger` and `DailySummary`.
5. Wire them up in `initialize`.

The inlined code MUST match `_lib` exactly except for class
renaming. The lint script (`scripts/lint_strategy.py`) verifies
this.

## How tests use _lib

`tests/mocks/AlgorithmImports.py` provides minimal `OrderEvent`,
`OrderStatus`, `OrderDirection`, `Slippage`, etc. stubs that allow
`_lib` modules to be imported and exercised offline. See
`tests/test_lib_*.py`.
