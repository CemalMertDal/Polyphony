#!/usr/bin/env python3
"""Focused tests for latest Gemini Flash effort resolution."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "resolve_flash_model", ROOT / "scripts" / "resolve-flash-model.py"
)
assert SPEC and SPEC.loader
resolver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resolver)


class FlashRoutingTests(unittest.TestCase):
    MODELS = """\
gemini-3.8-flash-high\tGemini 3.8 Flash (High)
gemini-3.8-flash-medium\tGemini 3.8 Flash (Medium)
gemini-3.8-flash-low\tGemini 3.8 Flash (Low)
gemini-3.9-flash-high\tGemini 3.9 Flash (High)
gemini-3.9-flash-medium\tGemini 3.9 Flash (Medium)
gemini-4.0-flash-high-preview\tGemini 4.0 Flash (High Preview)
claude-sonnet-4-6\tClaude Sonnet 4.6
"""

    def test_selects_latest_matching_effort(self):
        self.assertEqual(
            resolver.newest_model(self.MODELS, "medium"),
            "gemini-3.9-flash-medium",
        )
        self.assertEqual(
            resolver.newest_model(self.MODELS, "high"),
            "gemini-3.9-flash-high",
        )

    def test_ignores_low_preview_and_other_model_families(self):
        only_unsupported = """\
gemini-9.0-flash-low\tGemini 9.0 Flash (Low)
gemini-9.0-flash-high-preview\tGemini 9.0 Flash (High Preview)
gpt-oss-120b-medium\tGPT-OSS 120B (Medium)
"""
        self.assertIsNone(resolver.newest_model(only_unsupported, "medium"))
        self.assertIsNone(resolver.newest_model(only_unsupported, "high"))

    def test_parses_display_name_only_output(self):
        self.assertEqual(
            resolver.newest_model("Gemini 3.8 Flash (Medium)\n", "medium"),
            "gemini-3.8-flash-medium",
        )


if __name__ == "__main__":
    unittest.main()
