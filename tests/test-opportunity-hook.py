#!/usr/bin/env python3
"""Claude and Codex payload tests for the advisory reminder hook."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "agy_opportunity_reminder.py"


class OpportunityHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = os.environ.copy()
        self.env["AGY_QUOTA_STATE_DIR"] = self.temp.name

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, payload):
        completed = subprocess.run(
            [sys.executable, str(HOOK)],
            env=self.env,
            input=json.dumps(payload),
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip()

    def quota_state(self, decision=None):
        Path(self.temp.name, "state.json").write_text(
            json.dumps({
                "depleted": True,
                "decision": decision,
                "windows": {
                    "5h": {"remaining": 1.5},
                    "7d": {"remaining": 40},
                },
            }),
            encoding="utf-8",
        )

    def test_claude_read_warns_without_blocking(self):
        output = self.invoke(
            {
                "hook_event_name": "PreToolUse",
                "session_id": str(uuid.uuid4()),
                "tool_name": "Read",
                "tool_input": {"file_path": "src/app.py"},
            }
        )
        data = json.loads(output)
        hook = data["hookSpecificOutput"]
        self.assertEqual(hook["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", hook)
        self.assertIn("agy-scout", hook["additionalContext"])

    def test_codex_tool_names_cover_shell_patch_web_and_media(self):
        cases = [
            ("exec_command", {"cmd": "git push"}, "Git"),
            ("apply_patch", {"command": "*** Begin Patch"}, "dosya"),
            ("web__run", {"query": "topic"}, "web"),
            ("view_image", {"path": "x.png"}, "görsel"),
        ]
        for tool_name, tool_input, marker in cases:
            with self.subTest(tool_name=tool_name):
                output = self.invoke(
                    {
                        "hook_event_name": "PreToolUse",
                        "session_id": str(uuid.uuid4()),
                        "turn_id": "turn-1",
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                    }
                )
                self.assertIn(marker, json.loads(output)["hookSpecificOutput"]["additionalContext"])

    def test_same_category_warns_once_per_codex_turn(self):
        session = str(uuid.uuid4())
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": session,
            "turn_id": "one",
            "tool_name": "exec_command",
            "tool_input": {"cmd": "git push"},
        }
        self.assertTrue(self.invoke(payload))
        self.assertEqual(self.invoke(payload), "")
        payload["turn_id"] = "two"
        self.assertTrue(self.invoke(payload))

    def test_agy_calls_are_exempt(self):
        output = self.invoke(
            {
                "hook_event_name": "PreToolUse",
                "session_id": str(uuid.uuid4()),
                "tool_name": "exec_command",
                "tool_input": {"cmd": "agy-delegate --tier flash test"},
            }
        )
        self.assertEqual(output, "")

    def test_depleted_quota_prompts_for_an_explicit_choice_in_english(self):
        self.quota_state()
        output = self.invoke({
            "hook_event_name": "UserPromptSubmit",
            "session_id": str(uuid.uuid4()),
            "prompt": "continue",
        })
        context = json.loads(output)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("kill any active Agy workers", context)
        self.assertIn("check both quotas every 10 minutes", context)
        self.assertIn("only the user's explicit choice", context)

    def test_wait_choice_forbids_kill_and_sonnet(self):
        self.quota_state("wait")
        output = self.invoke({
            "hook_event_name": "PreToolUse",
            "session_id": str(uuid.uuid4()),
            "tool_name": "exec_command",
            "tool_input": {"cmd": "git status"},
        })
        context = json.loads(output)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Do not kill active Agy workers", context)
        self.assertIn("every 10 minutes", context)

    def test_sonnet_choice_requests_scoped_cancellation(self):
        self.quota_state("sonnet")
        output = self.invoke({
            "hook_event_name": "PreToolUse",
            "session_id": str(uuid.uuid4()),
            "tool_name": "exec_command",
            "tool_input": {"cmd": "git status"},
        })
        context = json.loads(output)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("user approved", context)
        self.assertIn("agy-job cancel-all", context)

    def test_codex_mcp_choice_recording_is_not_nagged(self):
        self.quota_state()
        output = self.invoke({
            "hook_event_name": "PreToolUse",
            "session_id": str(uuid.uuid4()),
            "tool_name": "mcp__antigravity__quota",
            "tool_input": {"action": "choose_sonnet"},
        })
        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
