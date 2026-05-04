"""
Canonical risk controls for Codex-generated strategies.

Per `.codex/AGENTS.md` Section 5 / engineer role: every strategy MUST
hard-stop trading for the session if drawdown from session peak equity
exceeds 20 percent.

Marker constant (do not rename or remove):
- DRAWDOWN_HARD_STOP_FRAC
"""

from __future__ import annotations


DRAWDOWN_HARD_STOP_FRAC: float = 0.20


class DrawdownStop:
    """
    Tracks high-water mark equity and signals a hard stop when
    current equity drops below the configured fraction.

    Default fraction is 20 percent. Lower values are allowed; higher
    values are not (the rule is a maximum, not a minimum).

    Usage skeleton:

        self.dd_stop = DrawdownStop()

        def on_data(self, slice):
            self.dd_stop.update(self.portfolio.total_portfolio_value)
            if self.dd_stop.tripped:
                if self.portfolio.invested:
                    self.liquidate()
                return
            ...
    """

    DEFAULT_HARD_STOP_FRAC: float = DRAWDOWN_HARD_STOP_FRAC

    def __init__(self, hard_stop_frac: float | None = None) -> None:
        frac = (
            self.DEFAULT_HARD_STOP_FRAC
            if hard_stop_frac is None
            else float(hard_stop_frac)
        )
        if not 0.0 < frac <= self.DEFAULT_HARD_STOP_FRAC:
            raise ValueError(
                "hard_stop_frac must be in (0, "
                f"{self.DEFAULT_HARD_STOP_FRAC}]; tighter is allowed, "
                "looser is not."
            )
        self._frac: float = frac
        self._peak: float | None = None
        self._tripped: bool = False

    @property
    def hard_stop_frac(self) -> float:
        return self._frac

    @property
    def peak(self) -> float | None:
        return self._peak

    @property
    def tripped(self) -> bool:
        return self._tripped

    def update(self, equity: float) -> bool:
        equity = float(equity)
        if self._peak is None or equity > self._peak:
            self._peak = equity
        if self._peak > 0.0:
            drawdown = (self._peak - equity) / self._peak
            if drawdown >= self._frac:
                self._tripped = True
        return self._tripped

    def reset(self) -> None:
        self._peak = None
        self._tripped = False


__all__ = [
    "DRAWDOWN_HARD_STOP_FRAC",
    "DrawdownStop",
]
