"""Unit tests for `scripts/lint_strategy.py`."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lint_strategy  # noqa: E402


# Canonical class snippets the engineer prompt instructs to inline.
TAKER_FEE = '''class BinanceUMTakerFeeModel(FeeModel):
    PER_SIDE_RATE: float = 0.0004
    TIER: str = "T"

    def get_order_fee(self, parameters):
        notional = abs(parameters.order.absolute_quantity) * float(
            parameters.security.price
        )
        return OrderFee(CashAmount(self.PER_SIDE_RATE * notional, "USD"))
'''

MAKER_FEE = '''class BinanceUMMakerFeeModel(FeeModel):
    PER_SIDE_RATE: float = 0.0002
    TIER: str = "M"

    def get_order_fee(self, parameters):
        notional = abs(parameters.order.absolute_quantity) * float(
            parameters.security.price
        )
        return OrderFee(CashAmount(self.PER_SIDE_RATE * notional, "USD"))
'''

TAKER_SLIPPAGE = '''class BinanceUMTakerSlippageModel(SlippageModel):
    PER_SIDE_RATE: float = 0.0005
    TIER: str = "T"

    def get_slippage_approximation(self, asset, order):
        return self.PER_SIDE_RATE * float(asset.price)
'''

MAKER_SIGNAL_GATE = '''class MakerSignalGate:
    DEFAULT_ADVERSE_THRESHOLD_BP: float = 5.0

    def __init__(self, adverse_threshold_bp=None):
        self._threshold = (
            self.DEFAULT_ADVERSE_THRESHOLD_BP
            if adverse_threshold_bp is None
            else float(adverse_threshold_bp)
        )
        self._pending = {}

    def submit(self, symbol, side, limit_price, quantity):
        self._pending[symbol] = (side, limit_price, quantity)

    def resolve(self, symbol, bar):
        return ("pending", 0.0)
'''

DRAWDOWN_STOP = '''class DrawdownStop:
    DEFAULT_HARD_STOP_FRAC: float = 0.20

    def __init__(self, hard_stop_frac=None):
        self._frac = (
            self.DEFAULT_HARD_STOP_FRAC
            if hard_stop_frac is None
            else float(hard_stop_frac)
        )
        self._peak = None
        self._tripped = False

    def update(self, equity):
        if self._peak is None or equity > self._peak:
            self._peak = equity
        return self._tripped
'''

VALID_TAKER_MAIN = (
    "# PROFILE: A-Taker\n"
    "from AlgorithmImports import *\n"
    "\n"
    "ENTRY_THRESHOLD: float = 0.005\n"
    "EXIT_THRESHOLD: float = 0.002\n"
    "MAX_HOLDING_BARS: int = 12\n"
    "\n"
    + TAKER_FEE
    + "\n"
    + TAKER_SLIPPAGE
    + "\n"
    + DRAWDOWN_STOP
    + "\n"
    "class MyAlgo(QCAlgorithm):\n"
    "    def initialize(self):\n"
    "        self.set_start_date(2025, 1, 1)\n"
)


VALID_MAKER_MAIN = (
    "# PROFILE: A-Maker\n"
    "from AlgorithmImports import *\n"
    "\n"
    "ENTRY_LIMIT_OFFSET_BP: float = 5.0\n"
    "ADVERSE_THRESHOLD_BP: float = 5.0\n"
    "MAX_HOLDING_BARS: int = 12\n"
    "\n"
    + MAKER_FEE
    + "\n"
    + MAKER_SIGNAL_GATE
    + "\n"
    + DRAWDOWN_STOP
    + "\n"
    "class MyAlgo(QCAlgorithm):\n"
    "    def initialize(self):\n"
    "        self.set_start_date(2025, 1, 1)\n"
)


def _write(tmp_path: Path, source: str, name: str = "main.py") -> Path:
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


def test_valid_taker_passes(tmp_path: Path) -> None:
    path = _write(tmp_path, VALID_TAKER_MAIN)
    result = lint_strategy.lint_strategy(path)
    assert [f.code for f in result.findings] == []
    assert result.profile == "A-Taker"
    assert result.tier == "T"


def test_valid_maker_passes(tmp_path: Path) -> None:
    path = _write(tmp_path, VALID_MAKER_MAIN)
    result = lint_strategy.lint_strategy(path)
    assert [f.code for f in result.findings] == []
    assert result.profile == "A-Maker"
    assert result.tier == "M"


def test_missing_profile_tag(tmp_path: Path) -> None:
    bad = "from AlgorithmImports import *\n" + TAKER_FEE
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "MISSING_PROFILE_TAG" in codes


def test_unknown_profile(tmp_path: Path) -> None:
    bad = "# PROFILE: Z-Cryptid\n" + VALID_TAKER_MAIN.split("\n", 1)[1]
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "UNKNOWN_PROFILE" in codes


def test_disallowed_import(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        "import requests\n"
        + TAKER_FEE
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "DISALLOWED_IMPORT" in codes


def test_lib_import_blocked(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        "from strategies._lib.fee_models import BinanceUMTakerFeeModel\n"
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "DISALLOWED_IMPORT" in codes


def test_too_many_free_parameters(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        "P1: float = 0.001\n"
        "P2: float = 0.002\n"
        "P3: float = 0.003\n"
        "P4: float = 0.004\n"
        + TAKER_FEE
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "TOO_MANY_FREE_PARAMETERS" in codes


def test_taker_missing_fee_model(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "MISSING_CANONICAL_CLASS" in codes


def test_maker_missing_signal_gate(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Maker\n"
        "from AlgorithmImports import *\n"
        + MAKER_FEE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "MISSING_MAKER_SIGNAL_GATE" in codes


def test_rate_mismatch_caught(tmp_path: Path) -> None:
    tampered_fee = TAKER_FEE.replace("0.0004", "0.0001")
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        + tampered_fee
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "RATE_MISMATCH" in codes


def test_emoji_caught(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        "# yay \U0001f389\n"
        + TAKER_FEE
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "EMOJI_FORBIDDEN" in codes


def test_getattr_caught(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        "x = getattr(object(), 'foo', None)\n"
        + TAKER_FEE
        + TAKER_SLIPPAGE
        + DRAWDOWN_STOP
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "DYNAMIC_ATTR_ACCESS" in codes


def test_missing_drawdown_stop(tmp_path: Path) -> None:
    bad = (
        "# PROFILE: A-Taker\n"
        "from AlgorithmImports import *\n"
        + TAKER_FEE
        + TAKER_SLIPPAGE
    )
    path = _write(tmp_path, bad)
    result = lint_strategy.lint_strategy(path)
    codes = {f.code for f in result.findings}
    assert "MISSING_DRAWDOWN_STOP" in codes


def test_main_function_exit_codes(tmp_path: Path, capsys) -> None:
    valid_path = _write(tmp_path, VALID_TAKER_MAIN, name="ok.py")
    rc = lint_strategy.main([str(valid_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "LINT: PASS" in out

    bad_path = _write(tmp_path, "x = 1\n", name="bad.py")
    rc_bad = lint_strategy.main([str(bad_path)])
    assert rc_bad == 1
    out_bad = capsys.readouterr().out
    assert "LINT: FAIL" in out_bad


def test_json_output(tmp_path: Path, capsys) -> None:
    path = _write(tmp_path, VALID_TAKER_MAIN)
    rc = lint_strategy.main(["--json", str(path)])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("{")
    assert '"ok": true' in out
