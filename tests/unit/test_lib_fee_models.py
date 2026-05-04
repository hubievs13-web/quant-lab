"""Unit tests for `strategies/_lib/fee_models.py`."""

from __future__ import annotations

import pytest

from strategies._lib.fee_models import (
    BinanceUMMakerFeeModel,
    BinanceUMTakerFeeModel,
    TIER_M_PER_SIDE_FEE,
    TIER_T_PER_SIDE_FEE,
)
from tests.mocks.AlgorithmImports import (
    OrderFeeParameters,
    _MockOrder,
    _MockSecurity,
)


def _build_params(*, price: float, quantity: float) -> OrderFeeParameters:
    security = _MockSecurity(symbol="BTCUSDT", price=price)
    order = _MockOrder(
        symbol="BTCUSDT",
        direction=0,
        quantity=quantity,
        absolute_quantity=abs(quantity),
    )
    return OrderFeeParameters(security=security, order=order)


def test_taker_fee_per_side_rate_is_canonical() -> None:
    assert TIER_T_PER_SIDE_FEE == 0.0004
    assert BinanceUMTakerFeeModel.PER_SIDE_RATE == TIER_T_PER_SIDE_FEE
    assert BinanceUMTakerFeeModel.TIER == "T"


def test_maker_fee_per_side_rate_is_canonical() -> None:
    assert TIER_M_PER_SIDE_FEE == 0.0002
    assert BinanceUMMakerFeeModel.PER_SIDE_RATE == TIER_M_PER_SIDE_FEE
    assert BinanceUMMakerFeeModel.TIER == "M"


def test_taker_fee_on_typical_order() -> None:
    params = _build_params(price=50_000.0, quantity=0.01)
    fee = BinanceUMTakerFeeModel().get_order_fee(params)
    assert fee.value.amount == pytest.approx(0.0004 * 50_000.0 * 0.01)
    assert fee.value.currency == "USD"


def test_maker_fee_on_typical_order() -> None:
    params = _build_params(price=50_000.0, quantity=0.01)
    fee = BinanceUMMakerFeeModel().get_order_fee(params)
    assert fee.value.amount == pytest.approx(0.0002 * 50_000.0 * 0.01)
    assert fee.value.currency == "USD"


def test_fee_uses_absolute_quantity_for_short_orders() -> None:
    params = _build_params(price=50_000.0, quantity=-0.01)
    fee_taker = BinanceUMTakerFeeModel().get_order_fee(params)
    assert fee_taker.value.amount == pytest.approx(0.0004 * 50_000.0 * 0.01)
    fee_maker = BinanceUMMakerFeeModel().get_order_fee(params)
    assert fee_maker.value.amount == pytest.approx(0.0002 * 50_000.0 * 0.01)


def test_round_trip_taker_friction_matches_rules() -> None:
    notional = 100.0
    round_trip_fee = 2.0 * BinanceUMTakerFeeModel.PER_SIDE_RATE * notional
    assert round_trip_fee == pytest.approx(0.08)


def test_round_trip_maker_fee_matches_rules() -> None:
    notional = 100.0
    round_trip_fee = 2.0 * BinanceUMMakerFeeModel.PER_SIDE_RATE * notional
    assert round_trip_fee == pytest.approx(0.04)
