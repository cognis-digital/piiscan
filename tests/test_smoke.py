"""Smoke tests for PIISCAN. Standard library only, no network."""

import io
import json
import os
import sys
import tempfile
import unittest
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from piiscan import (  # noqa: E402
    TOOL_NAME,
    TOOL_VERSION,
    scan_column,
    scan_dataset,
    luhn_valid,
    classify_risk,
)
from piiscan.cli import main  # noqa: E402
from piiscan.core import load_csv  # noqa: E402

DEMO_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "demos",
    "01-basic",
    "customers_sample.csv",
)


class TestValidators(unittest.TestCase):
    def test_luhn_valid(self):
        self.assertTrue(luhn_valid("4111 1111 1111 1111"))
        self.assertTrue(luhn_valid("4012888888881881"))

    def test_luhn_invalid(self):
        self.assertFalse(luhn_valid("1234567890123456"))
        self.assertFalse(luhn_valid("123"))  # too short

    def test_classify_risk(self):
        self.assertEqual(classify_risk(0.3, 5), "NONE")
        self.assertEqual(classify_risk(0.95, 5), "CRITICAL")
        self.assertEqual(classify_risk(0.6, 2), "MEDIUM")


class TestEngine(unittest.TestCase):
    def test_email_column_detected(self):
        rep = scan_column("email", ["a@b.com", "c@d.org", "e@f.net"])
        self.assertTrue(rep.is_pii)
        self.assertEqual(rep.top_entity, "EMAIL")
        self.assertGreaterEqual(rep.max_confidence, 0.8)

    def test_credit_card_luhn_gate(self):
        # Valid Luhn -> detected
        good = scan_column("card", ["4111111111111111", "4012888888881881"])
        self.assertEqual(good.top_entity, "CREDIT_CARD")
        # Random 16-digit ids failing Luhn -> not a card
        bad = scan_column("order_no", ["1234567890123456", "1111111111111111"])
        entities = [f.entity for f in bad.findings if f.confidence >= 0.5]
        self.assertNotIn("CREDIT_CARD", entities)

    def test_ssn_validation(self):
        rep = scan_column("ssn", ["123-45-6789", "234-56-7890"])
        self.assertEqual(rep.top_entity, "US_SSN")
        # invalid area 000 should not validate
        bad = scan_column("misc", ["000-12-3456"])
        self.assertFalse(any(f.entity == "US_SSN" and f.confidence >= 0.5 for f in bad.findings))

    def test_non_pii_column(self):
        rep = scan_column("region", ["WEST", "EAST", "CENTRAL"])
        self.assertFalse(rep.is_pii)

    def test_dataset_rollup(self):
        cols = {
            "email": ["a@b.com", "c@d.org"],
            "region": ["WEST", "EAST"],
        }
        rep = scan_dataset("t", cols)
        self.assertEqual(rep.columns_scanned, 2)
        self.assertEqual(rep.pii_columns, 1)
        self.assertIn("EMAIL", rep.entity_rollup())


class TestCLI(unittest.TestCase):
    def test_version(self):
        self.assertEqual(TOOL_NAME, "piiscan")
        self.assertTrue(TOOL_VERSION)

    def test_scan_json_exit_code(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["scan", DEMO_CSV, "--format", "json"])
        # PII present in demo -> exit code 2
        self.assertEqual(code, 2)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["dataset"], "customers_sample.csv")
        self.assertGreater(data["pii_columns"], 0)
        self.assertIn("US_SSN", data["entity_rollup"])
        self.assertIn("CREDIT_CARD", data["entity_rollup"])

    def test_scan_table_runs(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["scan", DEMO_CSV, "--format", "table"])
        self.assertEqual(code, 2)
        self.assertIn("PIISCAN report", buf.getvalue())

    def test_missing_file(self):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = main(["scan", "/nonexistent/path/nope.csv"])
        self.assertEqual(code, 1)


class TestEdgeCases(unittest.TestCase):
    """Tests for input validation, error paths, and edge cases added during hardening."""

    # --- scan_column edge cases ---

    def test_scan_column_none_values(self):
        """scan_column with None values does not raise and has 0 samples scanned."""
        # Use a neutral column name so no name-hint fires.
        rep = scan_column("col_x", None)
        self.assertEqual(rep.samples_scanned, 0)
        self.assertFalse(rep.is_pii)

    def test_scan_column_all_none_or_blank(self):
        """Columns where every value is None or blank have 0 samples scanned."""
        # Neutral name avoids the name-hint path.
        rep = scan_column("col_y", [None, "", "   "])
        self.assertEqual(rep.samples_scanned, 0)
        self.assertFalse(rep.is_pii)

    def test_scan_column_empty_list(self):
        """Empty column with no name hint returns zero confidence."""
        rep = scan_column("order_id", [])
        self.assertEqual(rep.max_confidence, 0.0)
        self.assertFalse(rep.is_pii)

    # --- scan_dataset edge cases ---

    def test_scan_dataset_empty_columns(self):
        """Empty column dict returns a zero-column report."""
        rep = scan_dataset("empty_ds", {})
        self.assertEqual(rep.columns_scanned, 0)
        self.assertEqual(rep.pii_columns, 0)
        self.assertEqual(rep.entity_rollup(), {})

    def test_scan_dataset_none_columns(self):
        """None columns dict returns a zero-column report without crashing."""
        rep = scan_dataset("none_ds", None)
        self.assertEqual(rep.columns_scanned, 0)
        self.assertEqual(rep.pii_columns, 0)

    # --- load_csv edge cases ---

    def test_load_csv_bom_utf8(self):
        """load_csv handles UTF-8-with-BOM files (common Excel export)."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
        ) as f:
            # Write UTF-8 BOM + CSV content
            f.write(b"\xef\xbb\xbfname,email\r\nAlice,alice@example.com\r\n")
            fpath = f.name
        try:
            _, cols = load_csv(fpath)
            self.assertIn("name", cols)
            self.assertIn("email", cols)
            self.assertEqual(cols["email"], ["alice@example.com"])
        finally:
            os.unlink(fpath)

    def test_load_csv_sample_limit(self):
        """load_csv honours the sample limit and does not read extra rows."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as f:
            f.write("id,val\n")
            for i in range(20):
                f.write(f"{i},value{i}\n")
            fpath = f.name
        try:
            _, cols = load_csv(fpath, sample=5)
            self.assertEqual(len(cols["id"]), 5)
        finally:
            os.unlink(fpath)

    # --- CLI validation ---

    def test_cli_bad_sample(self):
        """--sample 0 should return exit code 1 with a clear error."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = main(["scan", DEMO_CSV, "--sample", "0"])
        self.assertEqual(code, 1)
        self.assertIn("--sample", buf.getvalue())

    def test_cli_bad_min_confidence_high(self):
        """--min-confidence 1.5 is out of range — should return exit code 1."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = main(["scan", DEMO_CSV, "--min-confidence", "1.5"])
        self.assertEqual(code, 1)
        self.assertIn("--min-confidence", buf.getvalue())

    def test_cli_bad_min_confidence_negative(self):
        """--min-confidence -0.1 is out of range — should return exit code 1."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = main(["scan", DEMO_CSV, "--min-confidence", "-0.1"])
        self.assertEqual(code, 1)

    def test_cli_no_subcommand_returns_1(self):
        """Invoking without a subcommand prints help and returns exit code 1."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
