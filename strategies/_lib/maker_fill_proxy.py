"""
Maker (Tier M) fill proxy with adverse-selection rule.

Per `obsidian/01_Rules/02_Fee_Slippage_Model.md`, a limit-order fill is
treated as honest only if both:

  1. The bar reached the limit price (low <= L for buy, high >= L for
     sell).
  2. The next bar moved further adverse to the fill side by at least
     0.05 percent.

Without rule 2, naive limit-fill bookkeeping in a backtest overstates
fill rate and produces fantasy P&L.

`MakerSignalGate` implements this filter at the algorithm level. It
does not subclass any QuantConnect fill or order model, so it works
both inline in `main.py` and offline in tests.

Usage skeleton (inline in main.py):

    self.maker_gate = MakerSignalGate(adverse_threshold_bp=5)

    def on_data(self, slice):
        for symbol in self.symbols:
            bar = slice.bars.get(symbol)
            if bar is None:
                continue

            # 1. Resolve any pending fills with the new bar.
            decision = self.maker_gate.resolve(symbol, bar)
            if decision.action == "fill":
                self.market_order(symbol, decision.signed_quantity)
            # decision.action == "expire" or "pending": do nothing

            # 2. Generate new signal if applicable.
            if self._signal_long(symbol, bar):
                self.maker_gate.submit(
                    symbol=symbol,
                    side=+1,
                    limit_price=self._buy_limit(bar),
                    quantity=self._size(symbol),
                )

The strategy is free to size positions, set limit prices, and decide
exit logic. The gate's only job is to model adverse selection on
entry.

Marker constants (do not rename or remove):
- MAKER_DEFAULT_ADVERSE_THRESHOLD_BP
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAKER_DEFAULT_ADVERSE_THRESHOLD_BP: float = 5.0


@dataclass
class _PendingSignal:
    side: int
    limit_price: float
    quantity: float


@dataclass
class FillDecision:
    """Result of `MakerSignalGate.resolve`."""

    action: str
    signed_quantity: float = 0.0
    fill_price: float = 0.0


class MakerSignalGate:
    """
    Filters maker entry signals through the adverse-selection rule.

    Lifecycle per symbol:

      submit(side, limit, qty)
          Strategy says it would place a limit at `limit`. Stored as
          a pending signal until the next bar.

      resolve(bar)
          Called on each new bar. Returns one of:
            FillDecision(action="pending")
                The bar did not touch the limit. The signal is dropped
                (this implementation is single-bar timeout). The
                strategy can resubmit on a fresh signal.
            FillDecision(action="expire")
                The bar touched the limit but did not move adverse.
                The fill is treated as fantasy and dropped. Strategy
                does NOT enter the position.
            FillDecision(action="fill", signed_quantity=..., fill_price=...)
                The bar touched the limit AND moved adverse by at
                least the threshold. The strategy enters the position
                at the limit price.

    `adverse_threshold_bp` is in basis points (5.0 means 0.05 percent).
    """

    DEFAULT_ADVERSE_THRESHOLD_BP: float = MAKER_DEFAULT_ADVERSE_THRESHOLD_BP

    def __init__(self, adverse_threshold_bp: float | None = None) -> None:
        threshold = (
            self.DEFAULT_ADVERSE_THRESHOLD_BP
            if adverse_threshold_bp is None
            else float(adverse_threshold_bp)
        )
        if threshold < 0.0:
            raise ValueError("adverse_threshold_bp must be non-negative")
        self._threshold_frac: float = threshold / 10_000.0
        self._pending: dict[Any, _PendingSignal] = {}

    @property
    def adverse_threshold_bp(self) -> float:
        return self._threshold_frac * 10_000.0

    def has_pending(self, symbol: Any) -> bool:
        return symbol in self._pending

    def submit(
        self,
        symbol: Any,
        side: int,
        limit_price: float,
        quantity: float,
    ) -> None:
        if side not in (-1, 1):
            raise ValueError("side must be +1 (long) or -1 (short)")
        if limit_price <= 0.0:
            raise ValueError("limit_price must be positive")
        if quantity <= 0.0:
            raise ValueError("quantity must be positive")
        self._pending[symbol] = _PendingSignal(
            side=int(side),
            limit_price=float(limit_price),
            quantity=float(quantity),
        )

    def resolve(self, symbol: Any, bar: Any) -> FillDecision:
        pending = self._pending.get(symbol)
        if pending is None:
            return FillDecision(action="pending")

        low = float(bar.low)
        high = float(bar.high)
        close = float(bar.close)

        side = pending.side
        limit = pending.limit_price

        touched = (side > 0 and low <= limit) or (side < 0 and high >= limit)
        if not touched:
            del self._pending[symbol]
            return FillDecision(action="pending")

        if side > 0:
            adverse = close <= limit * (1.0 - self._threshold_frac)
        else:
            adverse = close >= limit * (1.0 + self._threshold_frac)

        del self._pending[symbol]

        if not adverse:
            return FillDecision(action="expire")

        signed_quantity = float(side) * pending.quantity
        return FillDecision(
            action="fill",
            signed_quantity=signed_quantity,
            fill_price=limit,
        )


class BinanceUMMakerFillModel:
    """
    Marker class. The actual mechanics live in `MakerSignalGate`,
    which is the canonical implementation Codex must inline. This
    class exists so the linter can locate a Tier M strategy by class
    name and verify that `MakerSignalGate` is present alongside it.
    """

    TIER: str = "M"


__all__ = [
    "BinanceUMMakerFillModel",
    "FillDecision",
    "MAKER_DEFAULT_ADVERSE_THRESHOLD_BP",
    "MakerSignalGate",
]
