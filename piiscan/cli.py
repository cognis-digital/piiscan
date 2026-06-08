"""Command-line interface for PIISCAN.

Usage:
    piiscan scan <file.csv> [--format table|json] [--sample N] [--min-confidence F]
    piiscan --version

Exit codes:
    0  scan completed, no PII columns found
    2  scan completed, PII detected (useful for CI gates)
    1  error (bad args, file not found, parse failure)
"""

from __future__ import annotations

import argparse
import json
import sys

from . import TOOL_NAME, TOOL_VERSION
from .core import load_csv, scan_dataset, ScanReport


def _render_table(report: ScanReport, min_conf: float) -> str:
    lines: list[str] = []
    lines.append(f"PIISCAN report for dataset: {report.dataset}")
    lines.append(
        f"  columns scanned: {report.columns_scanned}   pii columns: {report.pii_columns}"
    )
    rollup = report.entity_rollup()
    if rollup:
        roll_str = ", ".join(f"{k}={v}" for k, v in sorted(rollup.items()))
        lines.append(f"  entity rollup: {roll_str}")
    lines.append("")
    header = f"{'COLUMN':<24}{'ENTITY':<16}{'CONF':>6}  {'RISK':<9}{'HITS':>8}"
    lines.append(header)
    lines.append("-" * len(header))
    any_row = False
    for col in report.column_reports:
        d = col.to_dict()
        if d["max_confidence"] < min_conf:
            continue
        any_row = True
        entity = d["top_entity"] or "-"
        top = col.findings[0] if col.findings else None
        hits = f"{top.hits}/{top.samples_scanned}" if top else "-"
        lines.append(
            f"{col.column[:23]:<24}{entity:<16}{d['max_confidence']:>6.2f}  "
            f"{d['risk']:<9}{hits:>8}"
        )
    if not any_row:
        lines.append("(no columns above confidence threshold)")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="PII discovery across warehouses and data lakes (data-side scanner).",
    )
    parser.add_argument(
        "--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}"
    )
    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="Scan a CSV file for PII.")
    scan.add_argument("path", help="Path to a CSV file to scan.")
    scan.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format."
    )
    scan.add_argument(
        "--sample", type=int, default=1000, help="Max rows to sample per column."
    )
    scan.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Hide columns below this confidence in output (table mode).",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "scan":
        parser.print_help()
        return 1

    try:
        dataset_name, columns = load_csv(args.path, sample=args.sample)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 1
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        print(f"error: could not read {args.path}: {exc}", file=sys.stderr)
        return 1

    report = scan_dataset(dataset_name, columns)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(_render_table(report, args.min_confidence))

    # CI-friendly: non-zero (2) when PII is detected.
    return 2 if report.pii_columns > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
