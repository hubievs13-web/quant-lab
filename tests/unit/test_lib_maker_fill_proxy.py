"""Unit tests for `strategies/_lib/maker_fill_proxy.py`."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from strategies._lib.maker_fill_proxy import (
    MAKER_DEFAULT_ADVERSE_THRESHOLD_BP,
    MakerSignalGate,
)


@dataclass
class Bar:
    high: float
    low: float
    close: float


def test_default_threshold_is_canonical() -> None:
    assert MAKER_DEFAULT_ADVERSE_THRESHOLD_BP == 5.0
    gate = MakerSignalGate()
    assert gate.adverse_threshold_bp == pytest.approx(5.0)


def test_negative_threshold_rejected() -> None:
    with pytest.raises(ValueError):
        MakerSignalGate(adverse_threshold_bp=-1.0)


def test_invalid_side_rejected() -> None:
    gate = MakerSignalGate()
    with pytest.raises(ValueError):
        gate.submit(symbol="X", side=0, limit_price=100.0, quantity=1.0)


def test_no_pending_returns_pending() -> None:
    gate = MakerSignalGate()
    decision = gate.resolve("X", Bar(high=100.0, low=90.0, close=95.0))
    assert decision.action == "pending"


def test_long_signal_no_touch_drops() -> None:
    gate = MakerSignalGate()
    gate.submit(symbol="X", side=+1, limit_price=90.0, quantity=1.0)
    decision = gate.resolve("X", Bar(high=100.0, low=95.0, close=98.0))
    assert decision.action == "pending"
    assert not gate.has_pending("X")


def test_long_signal_touch_no_adverse_expires() -> None:
    gate = MakerSignalGate(adverse_threshold_bp=5.0)
    gate.submit(symbol="X", side=+1, limit_price=100.0, quantity=2.0)
    decision = gate.resolve("X", Bar(high=101.0, low=99.5, close=100.0))
    assert decision.action == "expire"
    assert decision.signed_quantity == 0.0
    assert not gate.has_pending("X")


def test_long_signal_touch_with_adverse_fills() -> None:
    gate = MakerSignalGate(adverse_threshold_bp=5.0)
    gate.submit(symbol="X", side=+1, limit_price=100.0, quantity=2.0)
    decision = gate.resolve("X", Bar(high=101.0, low=99.0, close=99.0))
    assert decision.action == "fill"
    assert decision.signed_quantity == pytest.approx(2.0)
    assert decision.fill_price == pytest.approx(100.0)
    assert not gate.has_pending("X")


def test_short_signal_touch_no_adverse_expires() -> None:
    gate = MakerSignalGate(adverse_threshold_bp=5.0)
    gate.submit(symbol="X", side=-1, limit_price=100.0, quantity=2.0)
    decision = gate.resolve("X", Bar(high=100.5, low=99.0, close=100.0))
    assert decision.action == "expire"


def test_short_signal_touch_with_adverse_fills() -> None:
    gate = MakerSignalGate(adverse_threshold_bp=5.0)
    gate.submit(symbol="X", side=-1, limit_price=100.0, quantity=2.0)
    decision = gate.resolve("X", Bar(high=101.0, low=100.0, close=101.0))
    assert decision.action == "fill"
    assert decision.signed_quantity == pytest.approx(-2.0)
    assert decision.fill_price == pytest.approx(100.0)


def test_threshold_boundary_long() -> None:
    gate = MakerSignalGate(adverse_threshold_bp=10.0)

    gate.submit(symbol="X", side=+1, limit_price=100.0, quantity=1.0)
    decision = gate.resolve(
        "X",
        Bar(high=100.0, low=99.5, close=99.95),
    )
    assert decision.action == "expire"

    gate.submit(symbol="X", side=+1, limit_price=100.0, quantity=1.0)
    decision = gate.resolve(
        "X",
        Bar(high=100.0, low=99.0, close=99.9),
    )
    assert decision.action == "fill"


def test_resolve_clears_pending_even_on_no_touch() -> None:
    gate = MakerSignalGate()
    gate.submit(symbol="X", side=+1, limit_price=90.0, quantity=1.0)
    assert gate.has_pending("X")
    gate.resolve("X", Bar(high=100.0, low=95.0, close=97.0))
    assert not gate.has_pending("X")


def test_multiple_symbols_isolated() -> None:
    gate = MakerSignalGate()
    gate.submit(symbol="A", side=+1, limit_price=100.0, quantity=1.0)
    gate.submit(symbol="B", side=-1, limit_price=200.0, quantity=2.0)

    a_decision = gate.resolve("A", Bar(high=101.0, low=99.0, close=98.0))
    b_decision = gate.resolve("B", Bar(high=199.0, low=198.0, close=199.0))

    assert a_decision.action == "fill"
    assert b_decision.action == "pending"
