"""
Canonical reference implementations of the plumbing every Codex
generated QuantConnect strategy needs.

This package is intentionally NOT imported by the strategies' `main.py`
files: the QuantConnect web IDE expects a single-file paste-ready
algorithm. Instead, the engineer prompt instructs Codex to inline the
relevant classes byte-for-byte into `main.py`, and the lint script
(`scripts/lint_strategy.py`) verifies that the inlined classes match
the canonical version.

Modules:
- `fee_models`         Tier T and Tier M fee models.
- `slippage_models`    Tier T slippage model.
- `maker_fill_proxy`   Tier M maker fill model with adverse-selection
                       rule.
- `risk_controls`      Drawdown stop helper.
- `diagnostics`        Per-trade and daily summary loggers.
"""

from strategies._lib.diagnostics import (
    DAILY_SUMMARY_PREFIX,
    DailySummary,
    PerTradeLogger,
    TRADE_LOG_PREFIX,
    TradeRecord,
)
from strategies._lib.fee_models import (
    BinanceUMMakerFeeModel,
    BinanceUMTakerFeeModel,
    TIER_M_PER_SIDE_FEE,
    TIER_T_PER_SIDE_FEE,
)
from strategies._lib.maker_fill_proxy import (
    BinanceUMMakerFillModel,
    FillDecision,
    MAKER_DEFAULT_ADVERSE_THRESHOLD_BP,
    MakerSignalGate,
)
from strategies._lib.risk_controls import (
    DRAWDOWN_HARD_STOP_FRAC,
    DrawdownStop,
)
from strategies._lib.slippage_models import (
    BinanceUMTakerSlippageModel,
    TIER_T_PER_SIDE_SLIPPAGE,
)

__all__ = [
    "BinanceUMMakerFeeModel",
    "BinanceUMMakerFillModel",
    "BinanceUMTakerFeeModel",
    "BinanceUMTakerSlippageModel",
    "DAILY_SUMMARY_PREFIX",
    "DRAWDOWN_HARD_STOP_FRAC",
    "DailySummary",
    "DrawdownStop",
    "FillDecision",
    "MAKER_DEFAULT_ADVERSE_THRESHOLD_BP",
    "MakerSignalGate",
    "PerTradeLogger",
    "TIER_M_PER_SIDE_FEE",
    "TIER_T_PER_SIDE_FEE",
    "TIER_T_PER_SIDE_SLIPPAGE",
    "TRADE_LOG_PREFIX",
    "TradeRecord",
]
