"""Unit tests for `strategies/_lib/diagnostics.py`."""

from __future__ import annotations

import pytest

from strategies._lib.diagnostics import (
    DAILY_SUMMARY_PREFIX,
    DailySummary,
    PerTradeLogger,
    TRADE_LOG_PREFIX,
)


class _Sink:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, line: str) -> None:
        self.lines.append(line)


def test_per_trade_logger_format() -> None:
    sink = _Sink()
    logger = PerTradeLogger(sink)
    logger.record(
        timestamp="2026-04-29T13:00:00Z",
        symbol="ETHUSDT",
        side=1,
        entry_price=2000.0,
        exit_price=2010.0,
        holding_bars=12,
        reason="signal_exit",
        pre_fee_pnl=10.0,
        post_fee_pnl=8.5,
    )
    assert len(sink.lines) == 1
    line = sink.lines[0]
    assert line.startswith(TRADE_LOG_PREFIX + " ")
    assert "sym=ETHUSDT" in line
    assert "side=1" in line
    assert "bars=12" in line
    assert "reason=signal_exit" in line
    assert "pre_fee_pnl=10.000000" in line
    assert "post_fee_pnl=8.500000" in line


def test_per_trade_logger_appends_records() -> None:
    sink = _Sink()
    logger = PerTradeLogger(sink)
    for _ in range(3):
        logger.record(
            timestamp="t",
            symbol="X",
            side=-1,
            entry_price=1.0,
            exit_price=1.0,
            holding_bars=1,
            reason="r",
            pre_fee_pnl=0.0,
            post_fee_pnl=0.0,
        )
    assert len(logger.records) == 3
    assert len(sink.lines) == 3


def test_daily_summary_basic_aggregation() -> None:
    sink = _Sink()
    summary = DailySummary(sink)
    summary.on_trade(pre_fee_pnl=0.005, post_fee_pnl=0.003)
    summary.on_trade(pre_fee_pnl=-0.002, post_fee_pnl=-0.004)
    summary.on_trade(pre_fee_pnl=0.001, post_fee_pnl=0.0)
    summary.on_equity(200.0)
    summary.on_equity(210.0)
    summary.on_equity(195.0)
    summary.flush("2026-04-29")

    assert len(sink.lines) == 1
    line = sink.lines[0]
    assert line.startswith(DAILY_SUMMARY_PREFIX + " ")
    assert "trades=3" in line
    assert "win_rate=0.3333" in line
    assert "intraday_max_dd=" in line


def test_daily_summary_flush_resets_bucket() -> None:
    sink = _Sink()
    summary = DailySummary(sink)
    summary.on_trade(pre_fee_pnl=0.01, post_fee_pnl=0.01)
    summary.on_equity(100.0)
    summary.flush("2026-04-29")

    summary.flush("2026-04-30")
    assert "trades=0" in sink.lines[-1]
    assert "win_rate=0.0000" in sink.lines[-1]


def test_intraday_max_dd_tracked() -> None:
    sink = _Sink()
    summary = DailySummary(sink)
    summary.on_equity(100.0)
    summary.on_equity(110.0)
    summary.on_equity(99.0)
    summary.flush("d")
    line = sink.lines[0]
    expected_dd = (110.0 - 99.0) / 110.0
    assert f"intraday_max_dd={expected_dd:.4f}" in line
