"""Process QuantConnect backtest artifacts into Obsidian + experiments.csv.

Takes a raw directory containing whatever the user exported from
QuantConnect (overview.png, equity_curve.png, trades.csv, orders.csv,
logs.txt, report.pdf, statistics.txt or statistics.json, plus any
extras), and produces:

1. obsidian/04_Backtests/<BTID>_<HID>_<DATE>/
     - copies of every raw artifact (originals are NOT removed)
     - report.md (Obsidian-ready Markdown)
2. results/experiments.csv
     - a row appended (or updated by backtest_id) for the run

Verdict policy:
    The script does NOT issue a final PASS / FAIL / INCONCLUSIVE.
    It only produces a draft:
        FAIL_DRAFT
        INCONCLUSIVE_DRAFT
        READY_FOR_DEVIN_REVIEW
    The Devin chat issues the final verdict.

Missing files are explicitly recorded as MISSING in the report. Metrics
that cannot be extracted are written as UNKNOWN. Nothing is fabricated.

Usage:
    python scripts/process_qc_backtest.py \\
        --hypothesis H0007 \\
        --strategy S0007 \\
        --raw-dir results/raw/BT0007_H0007_2026-04-29 \\
        [--backtest-id BT0007] [--date 2026-04-29] \\
        [--repo-root .] [--symbols BTCUSDT,ETHUSDT] [--timeframe 1m] \\
        [--is-window 2024-01-01:2024-12-31] \\
        [--oos-window 2025-01-01:2025-12-31]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Files we know how to look at. Anything else in raw-dir is still copied.
KNOWN_FILES = {
    "overview.png",
    "equity_curve.png",
    "trades.csv",
    "orders.csv",
    "logs.txt",
    "report.pdf",
    "statistics.txt",
    "statistics.json",
}

# Primary evidence: machine-readable. Secondary: screenshots / pdf.
PRIMARY_EVIDENCE = {"trades.csv", "orders.csv", "logs.txt", "statistics.txt", "statistics.json"}
SECONDARY_EVIDENCE = {"overview.png", "equity_curve.png", "report.pdf"}

CSV_HEADER = [
    "hypothesis_id", "strategy_id", "backtest_id", "date", "symbols",
    "timeframe", "is_start", "is_end", "oos_start", "oos_end",
    "total_trades", "net_return", "sharpe", "max_drawdown", "win_rate",
    "profit_factor", "avg_trade_net", "avg_trade_prefee",
    "mc_p5_final_equity", "mc_p95_max_drawdown", "mc_prob_loss",
    "evidence_confidence", "verdict", "reason", "artifacts_path",
]

# Aliases for typical QC statistics labels seen in statistics.txt or JSON.
METRIC_ALIASES = {
    "total_trades":   ["total trades", "totaltrades", "total_orders", "total trades count"],
    "net_return":     ["net profit", "total net profit", "netprofit", "net_return"],
    "sharpe":         ["sharpe ratio", "sharpe"],
    "max_drawdown":   ["drawdown", "max drawdown", "maxdrawdown"],
    "win_rate":       ["win rate", "winrate"],
    "profit_factor":  ["profit factor", "profitfactor"],
    "avg_trade_net":  ["average trade", "avg trade", "average win", "expectancy", "avg_trade"],
}


@dataclass
class Extracted:
    metrics: dict[str, str] = field(default_factory=dict)  # str values; UNKNOWN if absent
    n_trades_csv: int | None = None
    notes: list[str] = field(default_factory=list)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Process QC backtest artifacts")
    p.add_argument("--hypothesis", required=True, help="e.g. H0007")
    p.add_argument("--strategy", required=True, help="e.g. S0007")
    p.add_argument("--raw-dir", required=True, type=Path)
    p.add_argument("--backtest-id", default=None, help="default: derived from raw-dir name or auto")
    p.add_argument("--date", default=None, help="YYYY-MM-DD; default: today")
    p.add_argument("--repo-root", default=".", type=Path)
    p.add_argument("--symbols", default="")
    p.add_argument("--timeframe", default="")
    p.add_argument("--is-window", default="", help="ISO_START:ISO_END")
    p.add_argument("--oos-window", default="", help="ISO_START:ISO_END")
    return p.parse_args(argv)


def split_window(s: str) -> tuple[str, str]:
    if ":" not in s:
        return ("", "")
    a, b = s.split(":", 1)
    return (a.strip(), b.strip())


def derive_backtest_id(raw_dir: Path, fallback_hyp: str) -> str:
    name = raw_dir.name
    m = re.match(r"(BT\d{4})_", name)
    if m:
        return m.group(1)
    return f"BT{fallback_hyp.lstrip('H')}"


def extract_from_statistics_json(path: Path, ex: Extracted) -> None:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        ex.notes.append(f"statistics.json: parse error: {e}")
        return
    flat: dict[str, str] = {}
    def walk(node: object, prefix: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                key = f"{prefix}.{k}" if prefix else str(k)
                walk(v, key)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{prefix}[{i}]")
        else:
            flat[prefix.lower()] = str(node)
    walk(data)
    for metric, aliases in METRIC_ALIASES.items():
        if ex.metrics.get(metric):
            continue
        for alias in aliases:
            for k, v in flat.items():
                if alias in k:
                    ex.metrics[metric] = v
                    break
            if ex.metrics.get(metric):
                break


def extract_from_statistics_txt(path: Path, ex: Extracted) -> None:
    try:
        text = path.read_text()
    except Exception as e:
        ex.notes.append(f"statistics.txt: read error: {e}")
        return
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pairs: list[tuple[str, str]] = []
    for line in lines:
        m = re.match(r"^([A-Za-z][A-Za-z0-9 _\-/%()]+?)[:\t]\s*(.+)$", line)
        if m:
            pairs.append((m.group(1).strip().lower(), m.group(2).strip()))
    for metric, aliases in METRIC_ALIASES.items():
        if ex.metrics.get(metric):
            continue
        for alias in aliases:
            for label, value in pairs:
                if alias == label or alias in label:
                    ex.metrics[metric] = value
                    break
            if ex.metrics.get(metric):
                break


def extract_trade_count(path: Path, ex: Extracted) -> None:
    try:
        with path.open() as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                ex.notes.append("trades.csv: empty")
                return
            count = sum(1 for _ in reader)
        ex.n_trades_csv = count
        if not ex.metrics.get("total_trades"):
            ex.metrics["total_trades"] = str(count)
    except Exception as e:
        ex.notes.append(f"trades.csv: read error: {e}")


def list_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise SystemExit(f"raw dir not found: {raw_dir}")
    return sorted(p for p in raw_dir.iterdir() if p.is_file())


def copy_artifacts(raw_dir: Path, dst_dir: Path, files: list[Path]) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in files:
        shutil.copy2(src, dst_dir / src.name)


def confidence(present_primary: list[str], present_secondary: list[str]) -> str:
    if present_primary:
        return "OK"
    if present_secondary:
        return "LOW_CONFIDENCE"
    return "NO_EVIDENCE"


def draft_verdict(ex: Extracted, present_primary: list[str], conf: str) -> tuple[str, str]:
    """Return (verdict_draft, reason)."""
    if conf == "NO_EVIDENCE":
        return ("INCONCLUSIVE_DRAFT", "no artifacts present")
    if conf == "LOW_CONFIDENCE":
        return ("INCONCLUSIVE_DRAFT", "screenshots only; no machine-readable artifacts")
    n = ex.n_trades_csv
    if n is None and ex.metrics.get("total_trades"):
        try:
            n = int(float(re.sub(r"[^0-9.\-]", "", ex.metrics["total_trades"]) or "0"))
        except ValueError:
            n = None
    if n is not None and n < 30:
        return ("FAIL_DRAFT", f"trade count {n} below swing minimum 30")
    if n is not None and n < 300:
        return ("INCONCLUSIVE_DRAFT", f"trade count {n} below intraday minimum 300")
    return ("READY_FOR_DEVIN_REVIEW", "primary artifacts present; criteria 1-6 to be evaluated by Devin")


def render_report(
    args: argparse.Namespace,
    backtest_id: str,
    date_str: str,
    files: list[Path],
    present_primary: list[str],
    present_secondary: list[str],
    missing: list[str],
    ex: Extracted,
    conf: str,
    verdict: str,
    reason: str,
) -> str:
    is_start, is_end = split_window(args.is_window)
    oos_start, oos_end = split_window(args.oos_window)
    lines: list[str] = []
    lines.append("---")
    lines.append(f"id: {backtest_id}")
    lines.append(f"hypothesis: {args.hypothesis}")
    lines.append(f"strategy: {args.strategy}")
    lines.append(f"date: {date_str}")
    lines.append(f"symbols: {args.symbols or 'UNKNOWN'}")
    lines.append(f"timeframe: {args.timeframe or 'UNKNOWN'}")
    lines.append(f"is_window: [{is_start or 'UNKNOWN'}, {is_end or 'UNKNOWN'}]")
    lines.append(f"oos_window: [{oos_start or 'UNKNOWN'}, {oos_end or 'UNKNOWN'}]")
    lines.append(f"evidence_confidence: {conf}")
    lines.append(f"verdict_draft: {verdict}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {backtest_id} — {args.hypothesis} run {date_str}")
    lines.append("")
    lines.append("## 1. Metadata")
    lines.append("")
    lines.append(f"- Hypothesis: `obsidian/02_Hypotheses/{args.hypothesis}_*.md`")
    lines.append(f"- Strategy:   `obsidian/03_Strategies/{args.strategy}_*.md`")
    lines.append(f"- Strategy code: `strategies/{args.hypothesis}_*/`")
    lines.append(f"- QC project: 30774195 (Lean v17685)")
    lines.append(f"- Symbols: {args.symbols or 'UNKNOWN'}")
    lines.append(f"- Timeframe: {args.timeframe or 'UNKNOWN'}")
    lines.append("")
    lines.append("## 2. Files")
    lines.append("")
    if files:
        for f in files:
            tag = ""
            if f.name in PRIMARY_EVIDENCE:
                tag = " (primary)"
            elif f.name in SECONDARY_EVIDENCE:
                tag = " (secondary)"
            lines.append(f"- {f.name}{tag}")
    else:
        lines.append("- (none)")
    lines.append("")
    if missing:
        lines.append("Missing well-known files:")
        lines.append("")
        for m in missing:
            lines.append(f"- MISSING: {m}")
        lines.append("")
    lines.append("Evidence policy: machine-readable files (trades.csv, orders.csv,")
    lines.append("logs.txt, statistics.*) are PRIMARY. Screenshots and report.pdf")
    lines.append("are SECONDARY. If only secondary evidence is present, this report")
    lines.append("is marked LOW_CONFIDENCE.")
    lines.append("")
    lines.append("## 3. Key Metrics (extracted from artifacts; UNKNOWN if not found)")
    lines.append("")
    metric_keys = list(METRIC_ALIASES.keys()) + ["avg_trade_prefee"]
    for k in metric_keys:
        v = ex.metrics.get(k, "UNKNOWN")
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("Pre-fee average trade is reconstructed by the user / Devin from")
    lines.append("the post-fee average trade plus the assumed round-trip friction")
    lines.append("(~0.18 percent) per `obsidian/01_Rules/02_Fee_Slippage_Model.md`.")
    lines.append("This script does NOT auto-reconstruct it.")
    lines.append("")
    lines.append("## 4. Falsification Criteria 1-6 (DRAFT, Devin confirms)")
    lines.append("")
    lines.append("| # | Criterion                                 | Observed | Pass |")
    lines.append("|---|-------------------------------------------|----------|------|")
    lines.append(f"| 1 | Trade count >= 300 (intraday) or 30 swing | {ex.metrics.get('total_trades','UNKNOWN')} | UNKNOWN |")
    lines.append(f"| 2 | OOS Sharpe > 1.0                          | {ex.metrics.get('sharpe','UNKNOWN')} | UNKNOWN |")
    lines.append(f"| 3 | OOS net avg trade > 0                     | {ex.metrics.get('avg_trade_net','UNKNOWN')} | UNKNOWN |")
    lines.append(f"| 4 | Max drawdown < 25 percent                 | {ex.metrics.get('max_drawdown','UNKNOWN')} | UNKNOWN |")
    lines.append(f"| 5 | Pre-fee avg trade >= 0.10 percent         | UNKNOWN  | UNKNOWN |")
    lines.append(f"| 6 | WR >= 50 percent IS+OOS, OR PF >= 1.25    | wr={ex.metrics.get('win_rate','UNKNOWN')}, pf={ex.metrics.get('profit_factor','UNKNOWN')} | UNKNOWN |")
    lines.append("")
    lines.append("## 5. Missing Data")
    lines.append("")
    if missing:
        for m in missing:
            lines.append(f"- {m}: not provided in raw dir.")
    else:
        lines.append("- (no well-known files missing)")
    if ex.notes:
        lines.append("")
        lines.append("Parsing notes:")
        lines.append("")
        for n in ex.notes:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("## 6. Diagnostics")
    lines.append("")
    lines.append("Items to verify in logs.txt before sending to Devin:")
    lines.append("")
    lines.append("- signal-bar vs execution-bar timestamps (no leakage).")
    lines.append("- brokerage-model warnings (Binance Futures support).")
    lines.append("- data-gap or stale-quote warnings.")
    lines.append("- daily summaries emitted by the strategy.")
    lines.append("")
    lines.append("## 7. Preliminary Verdict Draft")
    lines.append("")
    lines.append(f"- evidence_confidence: {conf}")
    lines.append(f"- verdict_draft:       {verdict}")
    lines.append(f"- reason:              {reason}")
    lines.append("")
    lines.append("This is a DRAFT only. The Devin chat issues the final verdict.")
    lines.append("Possible draft values: FAIL_DRAFT, INCONCLUSIVE_DRAFT,")
    lines.append("READY_FOR_DEVIN_REVIEW.")
    lines.append("")
    lines.append("## 8. Notes for Devin")
    lines.append("")
    lines.append("- Primary evidence attached: " + (", ".join(present_primary) or "NONE"))
    lines.append("- Secondary evidence attached: " + (", ".join(present_secondary) or "NONE"))
    if conf == "LOW_CONFIDENCE":
        lines.append("- LOW_CONFIDENCE: only screenshots / pdf are present. Devin")
        lines.append("  should request CSV / log artifacts before issuing a verdict")
        lines.append("  beyond INCONCLUSIVE.")
    lines.append("- Apply Falsification Framework V3 criteria 1-6 to the metrics")
    lines.append("  above. If PRELIMINARY_PASS, request Monte Carlo run via")
    lines.append("  `scripts/monte_carlo.py` on the trades CSV.")
    lines.append("")
    return "\n".join(lines) + "\n"


def upsert_experiments_csv(
    csv_path: Path,
    args: argparse.Namespace,
    backtest_id: str,
    date_str: str,
    ex: Extracted,
    artifacts_path: Path,
    conf: str,
    verdict: str,
    reason: str,
) -> None:
    is_start, is_end = split_window(args.is_window)
    oos_start, oos_end = split_window(args.oos_window)
    row = {
        "hypothesis_id": args.hypothesis,
        "strategy_id": args.strategy,
        "backtest_id": backtest_id,
        "date": date_str,
        "symbols": args.symbols,
        "timeframe": args.timeframe,
        "is_start": is_start,
        "is_end": is_end,
        "oos_start": oos_start,
        "oos_end": oos_end,
        "total_trades": ex.metrics.get("total_trades", ""),
        "net_return": ex.metrics.get("net_return", ""),
        "sharpe": ex.metrics.get("sharpe", ""),
        "max_drawdown": ex.metrics.get("max_drawdown", ""),
        "win_rate": ex.metrics.get("win_rate", ""),
        "profit_factor": ex.metrics.get("profit_factor", ""),
        "avg_trade_net": ex.metrics.get("avg_trade_net", ""),
        "avg_trade_prefee": "",  # filled by user / Devin
        "mc_p5_final_equity": "",
        "mc_p95_max_drawdown": "",
        "mc_prob_loss": "",
        "evidence_confidence": conf,
        "verdict": verdict,
        "reason": reason,
        "artifacts_path": str(artifacts_path),
    }
    rows: list[dict[str, str]] = []
    if csv_path.exists():
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            for r in reader:
                # normalize to header
                rows.append({k: r.get(k, "") for k in CSV_HEADER})
    replaced = False
    for i, r in enumerate(rows):
        if r.get("backtest_id") == backtest_id:
            rows[i] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo_root.resolve()
    raw_dir = (args.raw_dir if args.raw_dir.is_absolute() else (repo / args.raw_dir)).resolve()
    if not raw_dir.exists():
        print(f"ERROR: --raw-dir not found: {raw_dir}", file=sys.stderr)
        return 2

    date_str = args.date or dt.date.today().isoformat()
    backtest_id = args.backtest_id or derive_backtest_id(raw_dir, args.hypothesis)

    folder_name = f"{backtest_id}_{args.hypothesis}_{date_str}"
    dst_dir = repo / "obsidian" / "04_Backtests" / folder_name
    files = list_raw_files(raw_dir)
    file_names = {p.name for p in files}
    missing = sorted(KNOWN_FILES - file_names)
    present_primary = sorted(PRIMARY_EVIDENCE & file_names)
    present_secondary = sorted(SECONDARY_EVIDENCE & file_names)

    ex = Extracted()
    if "statistics.json" in file_names:
        extract_from_statistics_json(raw_dir / "statistics.json", ex)
    if "statistics.txt" in file_names:
        extract_from_statistics_txt(raw_dir / "statistics.txt", ex)
    if "trades.csv" in file_names:
        extract_trade_count(raw_dir / "trades.csv", ex)

    # NOTE: do NOT setdefault metrics to "UNKNOWN" here. The CSV must keep
    # empty cells for unknown values (no fabrication). The report.md
    # rendering substitutes "UNKNOWN" only at display time.

    conf = confidence(present_primary, present_secondary)
    verdict, reason = draft_verdict(ex, present_primary, conf)

    copy_artifacts(raw_dir, dst_dir, files)
    report_path = dst_dir / "report.md"
    report_path.write_text(
        render_report(
            args, backtest_id, date_str, files,
            present_primary, present_secondary, missing,
            ex, conf, verdict, reason,
        )
    )

    csv_path = repo / "results" / "experiments.csv"
    upsert_experiments_csv(
        csv_path, args, backtest_id, date_str, ex,
        dst_dir.relative_to(repo), conf, verdict, reason,
    )

    print(f"backtest_id           : {backtest_id}")
    print(f"hypothesis            : {args.hypothesis}")
    print(f"strategy              : {args.strategy}")
    print(f"date                  : {date_str}")
    print(f"raw_dir               : {raw_dir}")
    print(f"obsidian_dir          : {dst_dir.relative_to(repo)}")
    print(f"report                : {report_path.relative_to(repo)}")
    print(f"experiments_csv       : {csv_path.relative_to(repo)}")
    print(f"present_primary       : {present_primary or 'NONE'}")
    print(f"present_secondary     : {present_secondary or 'NONE'}")
    print(f"missing_known_files   : {missing or 'NONE'}")
    print(f"evidence_confidence   : {conf}")
    print(f"verdict_draft         : {verdict}")
    print(f"reason                : {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
