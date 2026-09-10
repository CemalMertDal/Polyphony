#!/usr/bin/env python3
"""Deterministic tests for the shared Gemini 5h/7d quota state machine."""

from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "agy-quota.py"
SPEC = importlib.util.spec_from_file_location("polyphony_quota", SCRIPT)
assert SPEC and SPEC.loader
quota = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quota)


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env["AGY_QUOTA_STATE_DIR"] = str(self.root / "state")

    def tearDown(self):
        self.temp.cleanup()

    def usage(self, five_hour: float, weekly: float, name: str = "usage.txt") -> Path:
        path = self.root / name
        path.write_text(
            "Quota:\n"
            f"Gemini Models  Weekly Limit Remaining  {weekly}%  2026-09-17T00:00:00Z\n"
            f"Gemini Models  Five Hour Limit Remaining  {five_hour}%  2026-09-10T05:00:00Z\n",
            encoding="utf-8",
        )
        return path

    def invoke(self, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=self.env,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    @staticmethod
    def payload(output: str) -> dict:
        line = next(line for line in output.splitlines() if line.startswith("AGY_QUOTA "))
        return json.loads(line.removeprefix("AGY_QUOTA "))

    def test_either_decimal_window_at_or_below_two_is_depleted(self):
        result = self.invoke("--input", str(self.usage(1.5, 90)), "--json")
        self.assertEqual(result.returncode, 10, result.stderr)
        payload = self.payload(result.stdout)
        self.assertEqual(payload["status"], "DEPLETED")
        self.assertEqual(payload["gemini"]["5h"]["remaining"], 1.5)

        # Recovery of 5h is not enough when the weekly window is depleted.
        result = self.invoke("--input", str(self.usage(100, 2, "weekly.txt")), "--json")
        self.assertEqual(result.returncode, 10)
        self.assertEqual(self.payload(result.stdout)["gemini"]["7d"]["remaining"], 2.0)

    def test_threshold_alerts_are_per_window_and_not_repeated(self):
        self.assertEqual(self.invoke("--input", str(self.usage(80, 80))).returncode, 0)
        result = self.invoke("--input", str(self.usage(74, 49, "cross.txt")), "--alerts-only")
        self.assertIn("AGY_QUOTA_ALERT ", result.stdout)
        self.assertIn("Agy Gemini 5h quota has only 75% remaining.", result.stdout)
        self.assertIn("Agy Gemini 7d quota has only 50% remaining.", result.stdout)

        repeated = self.invoke("--input", str(self.usage(73, 48, "same-band.txt")))
        self.assertNotIn("quota has only", repeated.stdout)

        lower = self.invoke("--input", str(self.usage(24, 9, "lower.txt")))
        self.assertIn("Agy Gemini 5h quota has only 25% remaining.", lower.stdout)
        self.assertIn("Agy Gemini 7d quota has only 10% remaining.", lower.stdout)

    def test_user_choice_persists_only_until_recovery(self):
        self.assertEqual(
            self.invoke("--input", str(self.usage(1, 90)), "--json").returncode,
            10,
        )
        chosen = self.invoke("--decision", "sonnet", "--json")
        self.assertEqual(chosen.returncode, 0, chosen.stderr)
        self.assertEqual(self.payload(chosen.stdout)["decision"], "sonnet")

        still_depleted = self.invoke("--input", str(self.usage(1, 89, "same.txt")), "--json")
        self.assertEqual(self.payload(still_depleted.stdout)["decision"], "sonnet")

        recovered = self.invoke("--input", str(self.usage(100, 100, "reset.txt")), "--json")
        self.assertEqual(recovered.returncode, 0)
        self.assertIsNone(self.payload(recovered.stdout)["decision"])

    def test_environment_overrides_are_safe_and_effective(self):
        self.env["AGY_QUOTA_THRESHOLD"] = "3"
        result = self.invoke("--input", str(self.usage(2.5, 100)), "--json")
        self.assertEqual(result.returncode, 10)
        self.env["AGY_QUOTA_THRESHOLD"] = "not-a-number"
        result = self.invoke("--input", str(self.usage(2.5, 100, "default.txt")), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_usage_parser_accepts_ansi_spaced_and_missing_reset_text(self):
        parsed = quota.parse_usage(
            "\x1b[32mGemini Models  Weekly Limit Remaining  9.5%  resets in 2 days\x1b[0m\n"
            "Gemini Models  Five Hour Limit Remaining  1%\n"
        )
        self.assertEqual(parsed["7d"]["remaining"], 9.5)
        self.assertEqual(parsed["7d"]["reset_at"], "resets in 2 days")
        self.assertEqual(parsed["5h"]["reset_at"], "")


if __name__ == "__main__":
    unittest.main()
