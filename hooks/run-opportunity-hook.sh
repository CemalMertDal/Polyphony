#!/usr/bin/env bash
#
# Launcher for Claude Code hooks invoking agy_opportunity_reminder.py.
# Resolves AGY_BRIDGE_PYTHON first, then python3, py -3, python.
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HERE/agy_opportunity_reminder.py"

if [ -n "${AGY_BRIDGE_PYTHON:-}" ] && "$AGY_BRIDGE_PYTHON" -c 'import sys' >/dev/null 2>&1; then
  exec "$AGY_BRIDGE_PYTHON" "$TARGET" "$@"
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
  exec python3 "$TARGET" "$@"
elif command -v py >/dev/null 2>&1 && py -3 -c 'import sys' >/dev/null 2>&1; then
  exec py -3 "$TARGET" "$@"
elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
  exec python "$TARGET" "$@"
else
  exit 0
fi
