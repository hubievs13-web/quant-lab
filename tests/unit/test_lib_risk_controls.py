"""Unit tests for `strategies/_lib/risk_controls.py`."""

from __future__ import annotations

import pytest

from strategies._lib.risk_controls import DRAWDOWN_HARD_STOP_FRAC, DrawdownStop


def test_default_frac_is_canonical() -> None:
    assert DRAWDOWN_HARD_STOP_FRAC == 0.20


def test_default_constructor_uses_canonical() -> None:
    stop = DrawdownStop()
    assert stop.hard_stop_frac == pytest.approx(0.20)


def test_too_loose_frac_rejected() -> None:
    with pytest.raises(ValueError):
        DrawdownStop(hard_stop_frac=0.30)


def test_zero_or_negative_frac_rejected() -> None:
    with pytest.raises(ValueError):
        DrawdownStop(hard_stop_frac=0.0)
    with pytest.raises(ValueError):
        DrawdownStop(hard_stop_frac=-0.10)


def test_tighter_frac_allowed() -> None:
    stop = DrawdownStop(hard_stop_frac=0.10)
    assert stop.hard_stop_frac == pytest.approx(0.10)


def test_no_trip_on_growing_equity() -> None:
    stop = DrawdownStop()
    for equity in (100.0, 110.0, 120.0, 130.0):
        assert not stop.update(equity)
    assert not stop.tripped
    assert stop.peak == 130.0


def test_trips_at_threshold() -> None:
    stop = DrawdownStop(hard_stop_frac=0.20)
    stop.update(200.0)
    stop.update(180.0)
    assert not stop.tripped
    stop.update(160.0)
    assert stop.tripped


def test_remains_tripped_after_recovery() -> None:
    stop = DrawdownStop(hard_stop_frac=0.20)
    stop.update(200.0)
    stop.update(150.0)
    assert stop.tripped
    stop.update(220.0)
    assert stop.tripped


def test_reset_clears_state() -> None:
    stop = DrawdownStop(hard_stop_frac=0.20)
    stop.update(200.0)
    stop.update(150.0)
    assert stop.tripped
    stop.reset()
    assert not stop.tripped
    assert stop.peak is None
