"""Smoke tests for PIISCAN. Standard library only, no network."""

import io
import json
import os
import sys
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


if __name__ == "__main__":
    unittest.main()
