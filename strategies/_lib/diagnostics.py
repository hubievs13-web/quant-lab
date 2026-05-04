"""
Canonical diagnostics utilities.

Per `.codex/roles/engineer.md`, every strategy must emit:

- one log line per trade with: timestamp, symbol, side, entry price,
  exit price, holding bars, reason code, pre-fee PnL, post-fee PnL;
- a daily summary line with: trade count, win rate, average pre-fee
  edge, average post-fee edge, max intraday drawdown.

`PerTradeLogger` and `DailySummary` standardize these so the auditor
can grep for them in QC `Debug` output without per-strategy
formatting drift.

Marker constants (do not rename or remove):
- TRADE_LOG_PREFIX
- DAILY_SUMMARY_PREFIX
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


TRADE_LOG_PREFIX: str = "TRADE"
DAILY_SUMMARY_PREFIX: str = "DAILY_SUMMARY"


@dataclass
class TradeRecord:
    timestamp: Any
    symbol: Any
    side: int
    entry_price: float
    exit_price: float
    holding_bars: int
    reason: str
    pre_fee_pnl: float
    post_fee_pnl: float


class PerTradeLogger:
    """
    Emits one canonical line per closed trade. Calls `emit` (a
    callable provided at construction time, typically
    `algorithm.debug` or `algorithm.log`) so this class works both in
    QC and in offline tests.
    """

    PREFIX: str = TRADE_LOG_PREFIX

    def __init__(self, emit: Callable[[str], None]) -> None:
        self._emit = emit
        self._records: list[TradeRecord] = []

    @property
    def records(self) -> list[TradeRecord]:
        return list(self._records)

    def record(
        self,
        *,
        timestamp: Any,
        symbol: Any,
        side: int,
        entry_price: float,
        exit_price: float,
        holding_bars: int,
        reason: str,
        pre_fee_pnl: float,
        post_fee_pnl: float,
    ) -> None:
        record = TradeRecord(
            timestamp=timestamp,
            symbol=symbol,
            side=int(side),
            entry_price=float(entry_price),
            exit_price=float(exit_price),
            holding_bars=int(holding_bars),
            reason=str(reason),
            pre_fee_pnl=float(pre_fee_pnl),
            post_fee_pnl=float(post_fee_pnl),
        )
        self._records.append(record)
        self._emit(self._format(record))

    def _format(self, r: TradeRecord) -> str:
        return (
            f"{self.PREFIX} ts={r.timestamp} sym={r.symbol} side={r.side} "
            f"entry={r.entry_price:.6f} exit={r.exit_price:.6f} "
            f"bars={r.holding_bars} reason={r.reason} "
            f"pre_fee_pnl={r.pre_fee_pnl:.6f} "
            f"post_fee_pnl={r.post_fee_pnl:.6f}"
        )


@dataclass
class _DayBucket:
    trade_count: int = 0
    wins: int = 0
    pre_fee_pnl_sum: float = 0.0
    post_fee_pnl_sum: float = 0.0
    intraday_peak: float = 0.0
    intraday_max_dd: float = 0.0


class DailySummary:
    """
    Aggregates per-trade outcomes into a daily summary line. Driven
    by:

      - on_trade(...)  for each closed trade;
      - on_equity(equity_value) on each new bar to track intraday DD;
      - flush(date)    at end-of-day to emit the summary line.

    The intraday peak and DD reset on `flush`.
    """

    PREFIX: str = DAILY_SUMMARY_PREFIX

    def __init__(self, emit: Callable[[str], None]) -> None:
        self._emit = emit
        self._bucket: _DayBucket = _DayBucket()

    def on_trade(self, *, pre_fee_pnl: float, post_fee_pnl: float) -> None:
        self._bucket.trade_count += 1
        if post_fee_pnl > 0.0:
            self._bucket.wins += 1
        self._bucket.pre_fee_pnl_sum += float(pre_fee_pnl)
        self._bucket.post_fee_pnl_sum += float(post_fee_pnl)

    def on_equity(self, equity: float) -> None:
        equity = float(equity)
        if equity > self._bucket.intraday_peak:
            self._bucket.intraday_peak = equity
        if self._bucket.intraday_peak > 0.0:
            dd = (self._bucket.intraday_peak - equity) / self._bucket.intraday_peak
            if dd > self._bucket.intraday_max_dd:
                self._bucket.intraday_max_dd = dd

    def flush(self, date: Any) -> None:
        b = self._bucket
        win_rate = (b.wins / b.trade_count) if b.trade_count > 0 else 0.0
        avg_pre = (b.pre_fee_pnl_sum / b.trade_count) if b.trade_count > 0 else 0.0
        avg_post = (b.post_fee_pnl_sum / b.trade_count) if b.trade_count > 0 else 0.0
        line = (
            f"{self.PREFIX} date={date} trades={b.trade_count} "
            f"win_rate={win_rate:.4f} "
            f"avg_pre_fee={avg_pre:.6f} avg_post_fee={avg_post:.6f} "
            f"intraday_max_dd={b.intraday_max_dd:.4f}"
        )
        self._emit(line)
        self._bucket = _DayBucket()


__all__ = [
    "DAILY_SUMMARY_PREFIX",
    "DailySummary",
    "PerTradeLogger",
    "TRADE_LOG_PREFIX",
    "TradeRecord",
]
