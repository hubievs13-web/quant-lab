"""
Canonical slippage model for Tier T (taker) Binance USD-M Futures
backtests in QuantConnect Lean v17685.

Per `obsidian/01_Rules/02_Fee_Slippage_Model.md`, Tier T total
round-trip friction is approximately 0.18 percent. With 0.04 percent
per-side fee (= 0.08 percent round-trip), the slippage and impact
buffer must contribute the remaining 0.10 percent round-trip, i.e.,
0.05 percent per side.

This is inlined into a generated `main.py`. It is not imported from
`_lib` at runtime in QuantConnect.

Marker constant (do not rename or remove):
- TIER_T_PER_SIDE_SLIPPAGE
"""

from __future__ import annotations

try:
    from AlgorithmImports import SlippageModel  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - exercised only outside QC
    from tests.mocks.AlgorithmImports import SlippageModel


TIER_T_PER_SIDE_SLIPPAGE: float = 0.0005


class BinanceUMTakerSlippageModel(SlippageModel):
    """
    Per-side slippage of 0.05 percent of price. Combined with the
    0.04 percent per-side taker fee this yields approximately
    0.18 percent round-trip friction, matching the canonical Tier T
    figure.
    """

    PER_SIDE_RATE: float = TIER_T_PER_SIDE_SLIPPAGE
    TIER: str = "T"

    def get_slippage_approximation(self, asset, order) -> float:
        price = float(asset.price)
        return self.PER_SIDE_RATE * price


__all__ = [
    "BinanceUMTakerSlippageModel",
    "TIER_T_PER_SIDE_SLIPPAGE",
]
