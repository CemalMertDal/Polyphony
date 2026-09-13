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
                "8cfc264c8cf1808a58ce226e2443eb6b3c0af0abaaf7d0b43afc3777172966eb",
            SRC / "agy_headless_bridge" / "mcp_server.py":
                "3007479cbe244652668ed1508e5f6d623c750ae9d7b01cc8584f72aaf31d2e7b",
        }
        for path, digest in expected.items():
            # Git checkouts may use LF (Linux CI) or CRLF (native Windows). The
            # vendored source identity is line-ending independent for this pin.
            normalized = path.read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(normalized).hexdigest(), digest)
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
