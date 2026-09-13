<div align="center">

# Polyphony

**Multi-model orchestration for Claude Code and Codex, powered by Antigravity.**

![Polyphony — Claude and Codex orchestrate, Gemini executes](docs/hero.png)

Claude Code or Codex conducts the workflow. Gemini handles delegated execution through
a shared, verifiable toolchain.

</div>

---

## About

Polyphony gives Claude Code and Codex the same Antigravity (`agy`) worker toolkit. It
reduces main-agent context use while keeping execution scoped, observable, and verifiable.

- scoped implementation and general delegation
- read-only repository scouting and independent diff review
- web research and media analysis
- background jobs, 5h/7d quota control, traces, diagnostics, migration, Cloud debugging, and cost comparison
- non-blocking reminders when a task could be delegated to Gemini

On Windows, the bundled `agy-headless-bridge` v1.2.1 runs headless workers through ConPTY;
no separate bridge installation is required.

## Requirements

- [Antigravity CLI](https://antigravity.google/docs/cli-using) (`agy`), installed and authenticated, plus [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Codex, or both
- Python 3.9 or newer, with [pywinpty](https://pypi.org/project/pywinpty/) on Windows
- On Windows: Git Bash, included with [Git for Windows](https://git-scm.com/download/win), for the Bash wrappers

On native Windows, install `pywinpty` and authenticate Antigravity once:

```powershell
py -3 -m pip install -U pywinpty
agy
agy models
```

## Install for Claude Code

Run these commands inside Claude Code:

```text
/plugin marketplace add GryAsl/Polyphony
/plugin install antigravity@polyphony
/antigravity:setup
```

This installs the slash commands, skill, custom agent, wrappers, and optional delegation reminders.

## Install for Codex

```powershell
codex plugin marketplace add https://github.com/GryAsl/Polyphony
codex plugin add antigravity@polyphony
```

Start a new Codex task after installation. The plugin provides direct MCP tools for delegation, scouting, review, research, media, jobs, quota control, traces, diagnostics, migration, Cloud debugging, and cost comparison. Note that Codex plugin hooks must be reviewed and trusted whenever their definitions change.

## Routing modes

Polyphony provides two session-level routing modes:

- **Always use Agy (strict)**: Substantive native tool calls (discovery, code edits, diff review, tests/build/lint diagnosis, Git operations, web research, media analysis, native subagents, and general terminal automation) are blocked with PreToolUse denials. The turn requires a completed, successful Agy work call (exit code 0 with non-empty output) before stopping. External or unproven connectors remain advisory.
- **Use Agy when appropriate (soft)**: Non-blocking advisory reminders; native execution remains permitted.

**Default & session start:** Newly started, resumed, cleared, or forked sessions begin with routing mode unanswered and effective strict behavior (preserved across compact). At the first user-facing turn, the agent asks exactly one concise question presenting both canonical choices:
- Always use Agy (strict)
- Use Agy when appropriate (soft)
The user's initial substantive request remains in conversation and is resumed immediately after the choice.

**Control-plane exceptions:** Presenting the mode question, mode changes, quota checks/choices, job/trace/doctor/cancel management, bootstrap policy reading, and conversational user interaction are exempt from delegation gating.

**Manual switching:** Explicitly switch anytime with unambiguous phrasing such as "switch Agy mode to strict" or "set Agy mode to soft".

## Model routing

Calls default to High. Choose Medium explicitly only for a clearly simple task:

| Tier | Use it for | Model selection |
| --- | --- | --- |
| `flash` | Default; especially complex reasoning, architecture, concurrency/security, difficult debugging, ambiguous multi-file work, or adversarial review | Newest available Gemini Flash, High effort |
| `flash-medium` | Explicit option for simple, routine, mechanical, or tightly bounded work | Newest available Gemini Flash, Medium effort |
| `pro` | Exceptional escalation only | Configured Gemini Pro model |

There is no Low tier. Both Flash tiers query `agy models` and follow the newest available Gemini Flash family. If discovery is unavailable, they fall back to Gemini 3.8 Flash at the selected effort level. Exact models can still be supplied with `--model` or plugin configuration overrides.

## Usage

Claude Code examples:

```text
/antigravity:delegate --tier flash-medium "Add the missing unit tests"
/antigravity:delegate --tier flash "Diagnose this cross-module concurrency bug"
/antigravity:review
/antigravity:research "Research this topic and include source URLs"
/antigravity:quota
```

Codex uses the corresponding `antigravity` MCP tools directly. The MCP adapter calls the same wrappers and returns their stdout, stderr, and exact exit code.

The wrappers are also available from Git Bash:

```text
agy-delegate --tier flash-medium --dir "C:\path\to\repo" --digest "Implement this bounded change"
agy-scout --tier flash-medium --dir "C:\path\to\repo" "Trace the request flow"
agy-review --tier flash --dir "C:\path\to\repo" --staged --goal "Implement feature X"
agy-job start --tier flash --dir "C:\path\to\repo" "Complete this long-running task"
agy-quota --force
```

Routine calls default to 30 minutes. The Codex MCP transport allows 35 minutes so a healthy long-running worker can return before the transport closes. Use `--timeout` when a task needs a different wrapper deadline.

## Gemini quota control

The plugin reads Agy's zero-token `/usage` response and tracks both the Gemini **5h** and
**7d** windows. A failed, empty, or timed-out Gemini call triggers an immediate check.
If either window has **2% or less remaining**, the wrapper enters depleted mode and does
not switch models automatically.

Claude or Codex must ask the user to choose one of these paths:

1. Kill active Agy workers that are no longer progressing and continue the interrupted
   task with exact model `claude-sonnet-4-6`.
2. Keep the workers alive, wait for quota reset, and check both windows every 10 minutes.

Record the choice with `/antigravity:quota sonnet|wait`, `agy-quota --decision
sonnet|wait`, or the Codex `quota` MCP tool. `agy-job cancel-all` covers plugin-managed
jobs; the host must cancel any stalled tool tasks it started. Waiting resumes Gemini only
after both windows are above 2%.

The tracker emits a one-time notice when either window crosses 75%, 50%, 25%, or 10%
remaining. A threshold is not announced again until that quota window resets above it.

## Permissions and troubleshooting

Run write-capable tasks on a trusted branch. `--yolo` grants the worker broad access to
files, commands, network access, and process-visible credentials; it remains explicit
unless enabled in plugin or environment settings.

If a call fails, run `/antigravity:setup` in Claude Code, the `doctor` MCP tool in Codex, or `agy-doctor` from Git Bash. More diagnostics are in [Troubleshooting](docs/TROUBLESHOOTING.md).

## Why Polyphony uses ConPTY on Windows

[ConPTY](https://learn.microsoft.com/en-us/windows/console/pseudoconsoles) is the Windows
pseudoconsole system developed and maintained by Microsoft. It provides a bidirectional,
UTF-8 terminal channel for console applications—the Windows counterpart to a Unix PTY.
Polyphony uses ConPTY because headless Antigravity sessions still expect real terminal
semantics; ordinary redirected pipes can lose output, stall permission/tool flows, or
misrepresent an active process as hung. The bundled bridge hosts `agy` inside a genuine
Windows pseudoconsole while preserving structured output, Unicode, timeouts, and exit
codes for Claude Code and Codex.
