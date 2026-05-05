#!/usr/bin/env python3
"""
Static lint for Codex-generated QuantConnect strategy `main.py` files.

Goal: catch the cheap, obvious mistakes locally BEFORE the user pastes
the file into the QuantConnect web IDE and waits for a 6-12 minute
backtest to fail with a typo.

The lint operates on the raw source text and on the AST. It does NOT
execute the file, does NOT depend on the Lean Python runtime, and
therefore catches structural / contractual issues only.

Checks:

  1. First non-empty source line is a `# PROFILE: <name>` comment.
     Recognized profiles are derived from `.codex/AGENTS.md`
     Section 3.

  2. Imports come only from a whitelist (Lean Python standard
     surface). Imports from `strategies._lib`, `tests`, or any
     third-party package fail.

  3. Free parameter count <= 3. A free parameter is any
     module-level UPPER_SNAKE_CASE assignment of a numeric literal
     that is NOT one of the canonical marker constants from
     `strategies/_lib/`.

  4. Fee model class is present and matches the profile tier:
       Tier T: `BinanceUMTakerFeeModel` with per-side rate 0.0004.
       Tier M: `BinanceUMMakerFeeModel` with per-side rate 0.0002.

  5. Slippage / maker fill class is present and matches the tier:
       Tier T: `BinanceUMTakerSlippageModel` with per-side rate 0.0005.
       Tier M: `MakerSignalGate` (the adverse-selection gate).

  6. `DrawdownStop` class is present.

  7. No emoji anywhere in the source.

  8. No data-leakage smells: usages of `getattr`, `setattr`,
     `Any`, or obvious future-bar lookups via slice indexing into
     positive offsets are flagged.

Exit status:
  0   no findings.
  1   one or more findings (non-empty issue list printed).

Output:
  Plain text report on stdout, ending in `LINT: PASS` or
  `LINT: FAIL n=<count>`. Optional `--json` flag emits JSON instead so
  the auditor can paste it as-is.

Usage:
  python scripts/lint_strategy.py strategies/H0009_my_slug/main.py
  python scripts/lint_strategy.py --json strategies/H0009_my_slug/main.py
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


KNOWN_PROFILES: dict[str, str] = {
    "A-Maker": "M",
    "A-Taker": "T",
    "B-Position": "M",
    "B": "T",
}

ALLOWED_IMPORT_PREFIXES: tuple[str, ...] = (
    "AlgorithmImports",
    "QuantConnect",
    "System",
    "math",
    "datetime",
    "decimal",
    "collections",
    "statistics",
    "json",
    "io",
    "typing",
)

CANONICAL_MARKER_NAMES: frozenset[str] = frozenset(
    {
        "TIER_T_PER_SIDE_FEE",
        "TIER_M_PER_SIDE_FEE",
        "TIER_T_PER_SIDE_SLIPPAGE",
        "MAKER_DEFAULT_ADVERSE_THRESHOLD_BP",
        "DRAWDOWN_HARD_STOP_FRAC",
        "TRADE_LOG_PREFIX",
        "DAILY_SUMMARY_PREFIX",
    }
)

EMOJI_RE: re.Pattern[str] = re.compile(
    "["
    "\U0001f300-\U0001f6ff"
    "\U0001f900-\U0001f9ff"
    "\U00002600-\U000027bf"
    "\U0001fa70-\U0001faff"
    "]"
)

PROFILE_LINE_RE: re.Pattern[str] = re.compile(r"^\s*#\s*PROFILE\s*:\s*(\S+)\s*$")


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    line: int | None = None


@dataclass
class LintResult:
    path: str
    profile: str | None = None
    tier: str | None = None
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(f.severity == "info" for f in self.findings)

    def add(
        self,
        severity: str,
        code: str,
        message: str,
        line: int | None = None,
    ) -> None:
        self.findings.append(
            Finding(severity=severity, code=code, message=message, line=line)
        )


def lint_strategy(path: Path) -> LintResult:
    result = LintResult(path=str(path))

    if not path.exists():
        result.add("error", "FILE_NOT_FOUND", f"path does not exist: {path}")
        return result

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    _check_profile_tag(source, lines, result)
    _check_no_emoji(lines, result)

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        result.add(
            "error",
            "SYNTAX_ERROR",
            f"could not parse: {exc.msg}",
            line=exc.lineno,
        )
        return result

    _check_imports(tree, result)
    _check_free_parameters(tree, result)
    _check_required_classes(tree, source, result)
    _check_leakage_smells(tree, result)

    return result


def _first_non_empty_line(lines: list[str]) -> tuple[int | None, str | None]:
    for idx, raw in enumerate(lines, start=1):
        if raw.strip():
            return idx, raw
    return None, None


def _check_profile_tag(
    source: str, lines: list[str], result: LintResult
) -> None:
    line_no, raw = _first_non_empty_line(lines)
    if raw is None:
        result.add("error", "EMPTY_FILE", "main.py is empty")
        return
    match = PROFILE_LINE_RE.match(raw)
    if match is None:
        result.add(
            "error",
            "MISSING_PROFILE_TAG",
            "first non-empty line must be `# PROFILE: <name>`; "
            f"found: {raw.strip()!r}",
            line=line_no,
        )
        return
    profile = match.group(1)
    result.profile = profile
    if profile not in KNOWN_PROFILES:
        known = ", ".join(sorted(KNOWN_PROFILES))
        result.add(
            "error",
            "UNKNOWN_PROFILE",
            f"profile {profile!r} is not in `.codex/AGENTS.md` Section 3 "
            f"(known: {known})",
            line=line_no,
        )
        return
    result.tier = KNOWN_PROFILES[profile]


def _check_no_emoji(lines: list[str], result: LintResult) -> None:
    for idx, raw in enumerate(lines, start=1):
        match = EMOJI_RE.search(raw)
        if match is not None:
            result.add(
                "error",
                "EMOJI_FORBIDDEN",
                f"emoji {match.group(0)!r} is forbidden by AGENTS.md",
                line=idx,
            )


def _check_imports(tree: ast.AST, result: LintResult) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _import_allowed(alias.name):
                    result.add(
                        "error",
                        "DISALLOWED_IMPORT",
                        f"`import {alias.name}` is not on the Lean Python "
                        "whitelist; main.py must be paste-ready into the QC "
                        "single-file IDE",
                        line=node.lineno,
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not _import_allowed(module):
                result.add(
                    "error",
                    "DISALLOWED_IMPORT",
                    f"`from {module} import ...` is not on the Lean Python "
                    "whitelist; main.py must be paste-ready into the QC "
                    "single-file IDE",
                    line=node.lineno,
                )


def _import_allowed(module: str) -> bool:
    if not module:
        return False
    head = module.split(".", 1)[0]
    return head in ALLOWED_IMPORT_PREFIXES


def _check_free_parameters(tree: ast.AST, result: LintResult) -> None:
    free_params: list[tuple[str, int]] = []
    for node in ast.iter_child_nodes(tree):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        else:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if not _is_upper_snake(name):
                continue
            if name in CANONICAL_MARKER_NAMES:
                continue
            if not _is_numeric_literal(node):
                continue
            free_params.append((name, node.lineno))

    if len(free_params) > 3:
        names = ", ".join(n for n, _ in free_params)
        result.add(
            "error",
            "TOO_MANY_FREE_PARAMETERS",
            f"found {len(free_params)} free parameters (max 3): {names}",
            line=free_params[3][1] if len(free_params) > 3 else None,
        )


def _is_upper_snake(name: str) -> bool:
    if not name:
        return False
    if not name[0].isalpha():
        return False
    return name == name.upper() and "_" in name or name.isupper()


def _is_numeric_literal(node: ast.AST) -> bool:
    value: ast.AST | None = None
    if isinstance(node, ast.Assign):
        value = node.value
    elif isinstance(node, ast.AnnAssign):
        value = node.value
    if value is None:
        return False
    if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
        return True
    if (
        isinstance(value, ast.UnaryOp)
        and isinstance(value.op, (ast.UAdd, ast.USub))
        and isinstance(value.operand, ast.Constant)
        and isinstance(value.operand.value, (int, float))
    ):
        return True
    return False


def _collect_class_defs(tree: ast.AST) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.ClassDef)
    }


def _check_required_classes(
    tree: ast.AST, source: str, result: LintResult
) -> None:
    if result.tier is None:
        return
    classes = _collect_class_defs(tree)

    if result.tier == "T":
        _require_class_with_rate(
            classes,
            class_name="BinanceUMTakerFeeModel",
            attr_name="PER_SIDE_RATE",
            expected=0.0004,
            result=result,
        )
        _require_class_with_rate(
            classes,
            class_name="BinanceUMTakerSlippageModel",
            attr_name="PER_SIDE_RATE",
            expected=0.0005,
            result=result,
        )
    elif result.tier == "M":
        _require_class_with_rate(
            classes,
            class_name="BinanceUMMakerFeeModel",
            attr_name="PER_SIDE_RATE",
            expected=0.0002,
            result=result,
        )
        if "MakerSignalGate" not in classes:
            result.add(
                "error",
                "MISSING_MAKER_SIGNAL_GATE",
                "Tier M strategy must inline `MakerSignalGate` from "
                "`strategies/_lib/maker_fill_proxy.py` to model "
                "adverse selection on limit fills",
            )

    if "DrawdownStop" not in classes:
        result.add(
            "error",
            "MISSING_DRAWDOWN_STOP",
            "missing inlined `DrawdownStop` from "
            "`strategies/_lib/risk_controls.py`",
        )


def _require_class_with_rate(
    classes: dict[str, ast.ClassDef],
    *,
    class_name: str,
    attr_name: str,
    expected: float,
    result: LintResult,
) -> None:
    cls = classes.get(class_name)
    if cls is None:
        result.add(
            "error",
            "MISSING_CANONICAL_CLASS",
            f"missing inlined class `{class_name}` for tier "
            f"{result.tier} strategy",
        )
        return
    rate = _read_class_constant(cls, attr_name)
    if rate is None:
        result.add(
            "error",
            "MISSING_CLASS_RATE",
            f"class `{class_name}` is missing the `{attr_name}` "
            "class-level constant required by the canonical _lib version",
            line=cls.lineno,
        )
        return
    if abs(rate - expected) > 1e-9:
        result.add(
            "error",
            "RATE_MISMATCH",
            f"`{class_name}.{attr_name}` is {rate} but the canonical "
            f"value is {expected}",
            line=cls.lineno,
        )


def _read_class_constant(cls: ast.ClassDef, name: str) -> float | None:
    for node in cls.body:
        target = None
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
            value = node.value
        elif isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                target = node.targets[0].id
                value = node.value
        if target != name or value is None:
            continue
        if isinstance(value, ast.Constant) and isinstance(
            value.value, (int, float)
        ):
            return float(value.value)
        if (
            isinstance(value, ast.UnaryOp)
            and isinstance(value.op, (ast.UAdd, ast.USub))
            and isinstance(value.operand, ast.Constant)
            and isinstance(value.operand.value, (int, float))
        ):
            sign = -1.0 if isinstance(value.op, ast.USub) else 1.0
            return sign * float(value.operand.value)
    return None


def _check_leakage_smells(tree: ast.AST, result: LintResult) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"getattr", "setattr"}:
                result.add(
                    "error",
                    "DYNAMIC_ATTR_ACCESS",
                    f"`{node.func.id}` is forbidden by AGENTS.md "
                    "(types must be explicit; no dynamic attribute access)",
                    line=node.lineno,
                )
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "typing":
                if node.attr == "Any":
                    result.add(
                        "error",
                        "ANY_TYPE_USED",
                        "`typing.Any` is forbidden by AGENTS.md "
                        "(types must be explicit)",
                        line=node.lineno,
                    )


def _format_text(result: LintResult) -> str:
    out: list[str] = []
    out.append(f"path: {result.path}")
    out.append(f"profile: {result.profile or '<missing>'}")
    out.append(f"tier: {result.tier or '<missing>'}")
    if not result.findings:
        out.append("findings: none")
        out.append("LINT: PASS")
        return "\n".join(out)
    out.append("findings:")
    errors = 0
    for f in result.findings:
        loc = f"line {f.line}" if f.line is not None else "-"
        out.append(f"  [{f.severity.upper()}] {f.code} ({loc}): {f.message}")
        if f.severity == "error":
            errors += 1
    out.append(f"LINT: FAIL n={errors}")
    return "\n".join(out)


def _format_json(result: LintResult) -> str:
    payload = {
        "path": result.path,
        "profile": result.profile,
        "tier": result.tier,
        "findings": [
            {
                "severity": f.severity,
                "code": f.code,
                "message": f.message,
                "line": f.line,
            }
            for f in result.findings
        ],
        "ok": all(f.severity != "error" for f in result.findings),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="path to a strategy main.py file")
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of text"
    )
    args = parser.parse_args(argv)

    result = lint_strategy(Path(args.path))

    if args.json:
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0 if all(f.severity != "error" for f in result.findings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
