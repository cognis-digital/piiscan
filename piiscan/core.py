"""Core PII detection engine for PIISCAN.

The engine scans tabular datasets (columns of sampled values). Each detector
combines a column-name hint, a value-level regex, and an optional structural
validator. A column is matched against every detector; per-column and per-entity
rollups are produced with hit-rate driven confidence scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional


# --------------------------------------------------------------------------- #
# Structural validators
# --------------------------------------------------------------------------- #
def luhn_valid(number: str) -> bool:
    """Return True if ``number`` (digits, possibly spaced/dashed) passes Luhn."""
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


_INVALID_SSN_AREAS = {"000", "666"}


def ssn_valid(value: str) -> bool:
    """Validate US SSN area/group/serial rules (not just shape)."""
    m = re.match(r"^(\d{3})-?(\d{2})-?(\d{4})$", value.strip())
    if not m:
        return False
    area, group, serial = m.group(1), m.group(2), m.group(3)
    if area in _INVALID_SSN_AREAS or area.startswith("9"):
        return False
    if group == "00" or serial == "0000":
        return False
    return True


def ipv4_valid(value: str) -> bool:
    parts = value.strip().split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 and (p == "0" or not p.startswith("0")) for p in parts)
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Detector definition
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Detector:
    """A single PII entity detector.

    name      : entity type (e.g. ``EMAIL``)
    pattern   : compiled value-level regex (search over a value)
    name_hint : compiled regex tested against the column name
    validator : optional structural check applied to regex matches
    base_conf : base confidence when a value matches
    sensitivity: relative governance weight 1-5
    """

    name: str
    pattern: re.Pattern
    name_hint: Optional[re.Pattern] = None
    validator: Optional[Callable[[str], bool]] = None
    base_conf: float = 0.8
    sensitivity: int = 3

    def value_matches(self, value: str) -> bool:
        for m in self.pattern.finditer(value):
            if self.validator is None or self.validator(m.group(0)):
                return True
        return False

    def name_matches(self, column_name: str) -> bool:
        return bool(self.name_hint and self.name_hint.search(column_name))


def _ci(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


DEFAULT_DETECTORS: list[Detector] = [
    Detector(
        name="EMAIL",
        pattern=_ci(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}"),
        name_hint=_ci(r"e[-_]?mail|contact"),
        base_conf=0.95,
        sensitivity=3,
    ),
    Detector(
        name="US_SSN",
        pattern=re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
        name_hint=_ci(r"ssn|social.?sec|national.?id"),
        validator=ssn_valid,
        base_conf=0.97,
        sensitivity=5,
    ),
    Detector(
        name="CREDIT_CARD",
        pattern=re.compile(r"\b(?:\d[ -]?){13,19}\b"),
        name_hint=_ci(r"card|pan|cc[-_]?num|payment"),
        validator=luhn_valid,
        base_conf=0.9,
        sensitivity=5,
    ),
    Detector(
        name="PHONE",
        pattern=re.compile(
            r"(?:\+?1[ .\-]?)?\(?\d{3}\)?[ .\-]?\d{3}[ .\-]?\d{4}\b"
        ),
        name_hint=_ci(r"phone|mobile|cell|tel\b|telephone|fax"),
        base_conf=0.75,
        sensitivity=3,
    ),
    Detector(
        name="IPV4",
        pattern=re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
        name_hint=_ci(r"\bip\b|ip[-_]?addr|client[-_]?ip"),
        validator=ipv4_valid,
        base_conf=0.85,
        sensitivity=2,
    ),
    Detector(
        name="IBAN",
        pattern=re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
        name_hint=_ci(r"iban|bank.?acc|account.?num"),
        base_conf=0.85,
        sensitivity=5,
    ),
    Detector(
        name="DATE_OF_BIRTH",
        pattern=re.compile(r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b"),
        name_hint=_ci(r"dob|birth|date.?of.?birth"),
        base_conf=0.6,
        sensitivity=4,
    ),
    Detector(
        name="PERSON_NAME",
        pattern=re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}$"),
        name_hint=_ci(r"name|full.?name|first.?name|last.?name|surname"),
        base_conf=0.45,
        sensitivity=2,
    ),
]


# --------------------------------------------------------------------------- #
# Findings & reports
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    entity: str
    hits: int
    samples_scanned: int
    hit_rate: float
    confidence: float
    sensitivity: int
    name_hint_matched: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ColumnReport:
    column: str
    samples_scanned: int
    findings: list[Finding] = field(default_factory=list)

    @property
    def is_pii(self) -> bool:
        return any(f.confidence >= 0.5 for f in self.findings)

    @property
    def top_entity(self) -> Optional[str]:
        if not self.findings:
            return None
        return max(self.findings, key=lambda f: f.confidence).entity

    @property
    def max_confidence(self) -> float:
        return max((f.confidence for f in self.findings), default=0.0)

    @property
    def max_sensitivity(self) -> int:
        return max((f.sensitivity for f in self.findings if f.confidence >= 0.5), default=0)

    def to_dict(self) -> dict:
        return {
            "column": self.column,
            "samples_scanned": self.samples_scanned,
            "is_pii": self.is_pii,
            "top_entity": self.top_entity,
            "max_confidence": round(self.max_confidence, 3),
            "risk": classify_risk(self.max_confidence, self.max_sensitivity),
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ScanReport:
    dataset: str
    columns_scanned: int
    pii_columns: int
    column_reports: list[ColumnReport] = field(default_factory=list)

    def entity_rollup(self) -> dict[str, int]:
        roll: dict[str, int] = {}
        for col in self.column_reports:
            for f in col.findings:
                if f.confidence >= 0.5:
                    roll[f.entity] = roll.get(f.entity, 0) + 1
        return roll

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "columns_scanned": self.columns_scanned,
            "pii_columns": self.pii_columns,
            "entity_rollup": self.entity_rollup(),
            "columns": [c.to_dict() for c in self.column_reports],
        }


def classify_risk(confidence: float, sensitivity: int) -> str:
    """Combine confidence and entity sensitivity into a risk band."""
    if confidence < 0.5:
        return "NONE"
    score = confidence * sensitivity
    if score >= 4.0:
        return "CRITICAL"
    if score >= 2.5:
        return "HIGH"
    if score >= 1.2:
        return "MEDIUM"
    return "LOW"


# --------------------------------------------------------------------------- #
# Scanning
# --------------------------------------------------------------------------- #
def scan_column(
    column_name: str,
    values,
    detectors: Optional[list[Detector]] = None,
) -> ColumnReport:
    """Scan one column's sampled values against all detectors.

    ``values`` may be any iterable (list, tuple, generator).  ``None`` is
    treated as an empty column.  Non-string values are coerced to str.
    """
    detectors = detectors if detectors is not None else DEFAULT_DETECTORS
    if values is None:
        values = []
    try:
        raw = list(values)
    except TypeError:
        raw = []
    samples = [str(v) for v in raw if v is not None and str(v).strip() != ""]
    n = len(samples)
    report = ColumnReport(column=column_name, samples_scanned=n)

    for det in detectors:
        name_hit = det.name_matches(column_name)
        value_hits = sum(1 for v in samples if det.value_matches(v)) if n else 0
        hit_rate = (value_hits / n) if n else 0.0

        if value_hits == 0 and not name_hit:
            continue

        # Confidence: value evidence scaled by hit-rate, boosted by name hint.
        conf = 0.0
        if value_hits:
            conf = det.base_conf * (0.4 + 0.6 * hit_rate)
        if name_hit:
            # Column name alone is weak evidence; combined it is strong.
            conf = max(conf, 0.55) + (0.25 if value_hits else 0.0)
        conf = min(conf, 0.99)

        report.findings.append(
            Finding(
                entity=det.name,
                hits=value_hits,
                samples_scanned=n,
                hit_rate=round(hit_rate, 3),
                confidence=round(conf, 3),
                sensitivity=det.sensitivity,
                name_hint_matched=name_hit,
            )
        )

    report.findings.sort(key=lambda f: f.confidence, reverse=True)
    return report


def scan_dataset(
    dataset_name: str,
    columns: Optional[dict],
    detectors: Optional[list[Detector]] = None,
) -> ScanReport:
    """Scan a dataset given as a mapping of column name -> list of values.

    ``columns`` may be ``None`` or an empty dict — returns a zero-column report.
    """
    if not columns:
        return ScanReport(
            dataset=dataset_name or "",
            columns_scanned=0,
            pii_columns=0,
            column_reports=[],
        )
    column_reports = [
        scan_column(name, values, detectors) for name, values in columns.items()
    ]
    pii_cols = sum(1 for c in column_reports if c.is_pii)
    return ScanReport(
        dataset=dataset_name,
        columns_scanned=len(column_reports),
        pii_columns=pii_cols,
        column_reports=column_reports,
    )


def load_csv(path: str, sample: int = 1000) -> tuple[str, dict]:
    """Load a CSV file into a column->values mapping (sampling rows).

    Tries UTF-8-with-BOM first, then falls back to latin-1 so that files
    exported from Excel or Windows tools are handled without crashing.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If the file is empty, has no header row, or cannot be parsed as CSV.
    OSError / UnicodeDecodeError
        Propagated from the underlying file open.
    """
    import csv
    import os

    if sample < 1:
        raise ValueError(f"sample must be >= 1, got {sample}")

    def _read(enc: str) -> tuple[str, dict]:
        columns: dict[str, list] = {}
        with open(path, newline="", encoding=enc) as fh:
            reader = csv.DictReader(fh)
            # Trigger header read so we can check fieldnames.
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError(f"no header row in {path}")
            for c in fieldnames:
                columns[c] = []
            for i, row in enumerate(reader):
                if i >= sample:
                    break
                for c in fieldnames:
                    columns[c].append(row.get(c))
        return os.path.basename(path), columns

    try:
        return _read("utf-8-sig")
    except UnicodeDecodeError:
        return _read("latin-1")
