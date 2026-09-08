#!/usr/bin/env python3
"""Resolve the newest available Gemini Flash model for one effort level."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VENDORED_BRIDGE_SRC = ROOT / "vendor" / "agy-headless-bridge" / "src"
if VENDORED_BRIDGE_SRC.is_dir():
    sys.path.insert(0, str(VENDORED_BRIDGE_SRC))

from agy_headless_bridge import find_agy  # noqa: E402


SLUG = re.compile(
    r"(?<![a-z0-9-])gemini-(\d+(?:\.\d+)+)-flash-(medium|high)(?=\s|$)",
    re.IGNORECASE,
)
DISPLAY = re.compile(
    r"\bGemini\s+(\d+(?:\.\d+)+)\s+Flash\s*\((Medium|High)\)",
    re.IGNORECASE,
)


def newest_model(models: str, effort: str) -> str | None:
    candidates: list[tuple[tuple[int, ...], str]] = []
    wanted = effort.lower()
    for line in models.splitlines():
        match = SLUG.search(line) or DISPLAY.search(line)
        if not match or match.group(2).lower() != wanted:
            continue
        version = tuple(int(part) for part in match.group(1).split("."))
        candidates.append((version, f"gemini-{match.group(1)}-flash-{wanted}"))
    return max(candidates)[1] if candidates else None


def read_models(timeout: float) -> str | None:
    agy = find_agy()
    if not agy:
        return None
    output_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as output:
            output_path = output.name
            completed = subprocess.run(
                [agy, "models"],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                check=False,
            )
        if completed.returncode != 0:
            return None
        return Path(output_path).read_text(encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        if output_path:
            try:
                os.unlink(output_path)
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--effort", required=True, choices=("medium", "high"))
    parser.add_argument("--fallback", required=True)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--models-file", help="Parse a fixture instead of invoking agy")
    args = parser.parse_args()

    if args.models_file:
        try:
            models = Path(args.models_file).read_text(encoding="utf-8", errors="replace")
        except OSError:
            models = None
    else:
        models = read_models(args.timeout)
    print(newest_model(models or "", args.effort) or args.fallback)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
