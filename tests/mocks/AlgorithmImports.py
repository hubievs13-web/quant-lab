"""
Minimal mock of `AlgorithmImports` used by QuantConnect Lean v17685 in
its Python runtime. Exists ONLY for offline unit tests of the
`strategies/_lib/` reference implementations.

This is NOT a faithful reproduction of the Lean Python API. It exposes
just enough surface for the `_lib` modules to be importable and
exercisable in plain Python.

Tests that need this mock add `tests/mocks/` to `sys.path` before
importing `AlgorithmImports`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class OrderDirection(IntEnum):
    BUY = 0
    SELL = 1
    HOLD = 2


class OrderStatus(IntEnum):
    NEW = 0
    SUBMITTED = 1
    PARTIALLY_FILLED = 2
    FILLED = 3
    CANCELED = 4
    NONE = 5
    INVALID = 6


@dataclass
class CashAmount:
    amount: float
    currency: str = "USD"


@dataclass
class OrderFee:
    value: CashAmount


@dataclass
class _MockSecurity:
    symbol: str
    price: float = 0.0


@dataclass
class _MockOrder:
    symbol: str
    direction: OrderDirection
    quantity: float
    limit_price: float | None = None
    absolute_quantity: float | None = None

    def __post_init__(self) -> None:
        if self.absolute_quantity is None:
            self.absolute_quantity = abs(self.quantity)


@dataclass
class OrderFeeParameters:
    security: _MockSecurity
    order: _MockOrder


@dataclass
class SlippageContext:
    asset: _MockSecurity
    order: _MockOrder


class FeeModel:
    """Base class. Strategies subclass this and override `get_order_fee`."""

    def get_order_fee(self, parameters: OrderFeeParameters) -> OrderFee:
        raise NotImplementedError


class SlippageModel:
    """Base class. Strategies subclass this and override the approximation."""

    def get_slippage_approximation(
        self, asset: _MockSecurity, order: _MockOrder
    ) -> float:
        raise NotImplementedError


@dataclass
class TradeBar:
    time: Any
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


__all__ = [
    "CashAmount",
    "FeeModel",
    "OrderDirection",
    "OrderFee",
    "OrderFeeParameters",
    "OrderStatus",
    "SlippageContext",
    "SlippageModel",
    "TradeBar",
    "_MockOrder",
    "_MockSecurity",
]
