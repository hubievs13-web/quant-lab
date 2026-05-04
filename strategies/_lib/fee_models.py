"""
Canonical fee models for Binance USD-M Futures backtests in
QuantConnect Lean v17685.

Two tiers per `obsidian/01_Rules/02_Fee_Slippage_Model.md`:

- Tier T (taker, market orders): per-side fee 0.04 percent.
- Tier M (maker, limit orders): per-side fee 0.02 percent. No
  rebate is assumed.

These classes are inlined into the generated `main.py` by the
engineer prompt. They are not imported from `_lib` at runtime in
QuantConnect, because the QC web IDE expects a single file. The
linter (`scripts/lint_strategy.py`) verifies that the inlined
classes are present and structurally match the canonical version.

Marker constants (do not remove or rename) are read by the linter:
- TIER_T_PER_SIDE_FEE
- TIER_M_PER_SIDE_FEE
"""

from __future__ import annotations

try:
    from AlgorithmImports import (  # type: ignore[import-not-found]
        CashAmount,
        FeeModel,
        OrderFee,
        OrderFeeParameters,
    )
except ImportError:  # pragma: no cover - exercised only outside QC
    from tests.mocks.AlgorithmImports import (
        CashAmount,
        FeeModel,
        OrderFee,
        OrderFeeParameters,
    )


TIER_T_PER_SIDE_FEE: float = 0.0004
TIER_M_PER_SIDE_FEE: float = 0.0002


def _notional(parameters: OrderFeeParameters) -> float:
    """USD notional of the order at current security price."""
    quantity = parameters.order.absolute_quantity
    if quantity is None:
        quantity = abs(parameters.order.quantity)
    price = float(parameters.security.price)
    return float(abs(quantity)) * price


class BinanceUMTakerFeeModel(FeeModel):
    """
    Tier T fee: 0.04 percent of the order's notional, per side.

    Lean's fee model is called once per fill. We charge the
    fixed per-side rate; round-trip cost emerges from two fills
    (entry + exit).
    """

    PER_SIDE_RATE: float = TIER_T_PER_SIDE_FEE
    TIER: str = "T"

    def get_order_fee(self, parameters: OrderFeeParameters) -> OrderFee:
        fee = self.PER_SIDE_RATE * _notional(parameters)
        return OrderFee(CashAmount(fee, "USD"))


class BinanceUMMakerFeeModel(FeeModel):
    """
    Tier M fee: 0.02 percent of the order's notional, per side. No
    rebate. Fallback to Tier T friction is the strategy's
    responsibility when a limit order is canceled and re-submitted
    as a market order.
    """

    PER_SIDE_RATE: float = TIER_M_PER_SIDE_FEE
    TIER: str = "M"

    def get_order_fee(self, parameters: OrderFeeParameters) -> OrderFee:
        fee = self.PER_SIDE_RATE * _notional(parameters)
        return OrderFee(CashAmount(fee, "USD"))


__all__ = [
    "BinanceUMMakerFeeModel",
    "BinanceUMTakerFeeModel",
    "TIER_M_PER_SIDE_FEE",
    "TIER_T_PER_SIDE_FEE",
]
