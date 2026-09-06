#!/usr/bin/env python3
"""Pin the vendored bridge to the exact v1.2.1 source snapshot."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "agy-headless-bridge"
SRC = VENDOR / "src"


class VendoredBridgeTests(unittest.TestCase):
    def test_v121_source_hashes_and_license(self):
        expected = {
            SRC / "agy_headless_bridge" / "bridge.py":
                "a5e7df980cea50c7354a1884b4ca9f62bd9f6b866228c0c017a23650e29cc69f",
            SRC / "agy_headless_bridge" / "mcp_server.py":
                "d3af8f39a909ddf57987bf305b9198f3eb9bfb98cb0f641e21d45b172363977d",
        }
        for path, digest in expected.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        self.assertIn("MIT License", (VENDOR / "LICENSE").read_text(encoding="utf-8"))

    def test_package_imports_from_vendor_tree(self):
        sys.path.insert(0, str(SRC))
        try:
            import agy_headless_bridge
            self.assertEqual(agy_headless_bridge.__version__, "1.2.1")
        finally:
            sys.path.remove(str(SRC))


if __name__ == "__main__":
    unittest.main()
