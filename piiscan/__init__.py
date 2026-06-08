"""PIISCAN - PII discovery across warehouses and data lakes.

A data-side scanner that profiles column samples (and free text) to detect
personally identifiable information using a layered detector engine:

  1. Column-name heuristics (e.g. ``email``, ``ssn``, ``phone``)
  2. Value regex patterns (email, SSN, credit card, IP, phone, IBAN, ...)
  3. Structural validators (Luhn for cards, SSN area/group rules)

Findings are scored by hit-rate and confidence, then rolled up per column and
per entity type so governance teams can prioritize remediation.

Standard library only. Zero install.
"""

from .core import (
    Detector,
    Finding,
    ColumnReport,
    ScanReport,
    DEFAULT_DETECTORS,
    scan_column,
    scan_dataset,
    luhn_valid,
    classify_risk,
)

TOOL_NAME = "piiscan"
TOOL_VERSION = "1.0.0"

__all__ = [
    "Detector",
    "Finding",
    "ColumnReport",
    "ScanReport",
    "DEFAULT_DETECTORS",
    "scan_column",
    "scan_dataset",
    "luhn_valid",
    "classify_risk",
    "TOOL_NAME",
    "TOOL_VERSION",
]
