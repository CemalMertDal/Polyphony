<div align="center">

# Polyphony

**Multi-model orchestration for Claude Code and Codex, powered by Antigravity.**

![Polyphony — Claude and Codex orchestrate, Gemini executes](docs/hero.png)

Claude Code or Codex conducts the workflow. Gemini handles delegated execution through
a shared, verifiable toolchain.

</div>

---

## About

Polyphony is a community-built orchestration layer that gives Claude Code and Codex the
same production-minded Antigravity (`agy`) worker toolkit. It is designed to reduce main
agent context use while retaining explicit scope, observable execution, compact evidence,
and user-controlled fallback behavior.

- scoped implementation and general delegation
- read-only repository scouting and independent diff review
- web research and media analysis
- background jobs, 5h/7d quota control, traces, diagnostics, migration, Cloud debugging, and cost comparison
- non-blocking reminders when a task could be delegated to Gemini

Native Windows headless execution uses the bundled `agy-headless-bridge` v1.2.1 through Windows ConPTY. No separate bridge installation is required.

## Requirements

- [Antigravity CLI](https://antigravity.google/docs/cli-using) (`agy`), installed and authenticated
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Codex, or both
- Python 3.9 or newer
- [pywinpty](https://pypi.org/project/pywinpty/) on native Windows
- Git Bash, normally included with [Git for Windows](https://git-scm.com/download/win), because the wrappers are Bash scripts

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

The plugin installs its slash commands, Antigravity skill, custom agent, wrappers, and optional delegation-reminder hooks.

## Install for Codex

```powershell
codex plugin marketplace add https://github.com/GryAsl/Polyphony
codex plugin add antigravity@polyphony
```

Start a new Codex task after installation. Codex receives direct MCP tools for delegation, scouting, review, research, media, jobs, quota control, traces, diagnostics, migration, Cloud debugging, and cost comparison. Review and trust the optional non-blocking hooks from `/hooks`; Codex does not trust plugin hooks automatically.

## Model routing

Calls default to High. The caller may explicitly choose Medium for a clearly simple task:

| Tier | Use it for | Model selection |
| --- | --- | --- |
| `flash` | Default; especially complex reasoning, architecture, concurrency/security, difficult debugging, ambiguous multi-file work, or adversarial review | Newest available Gemini Flash, High effort |
| `flash-medium` | Explicit option for simple, routine, mechanical, or tightly bounded work | Newest available Gemini Flash, Medium effort |
| `pro` | Exceptional escalation only | Configured Gemini Pro model |

There is no Low tier. Both Flash tiers query `agy models` and automatically follow the newest available Gemini Flash family. If discovery is unavailable, version 0.30.0 falls back to Gemini 3.8 Flash at the selected effort level. Exact models can still be supplied with `--model` or the plugin configuration overrides.

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

Claude or Codex must ask the user—in English—to choose one of these paths:

1. Kill active Agy workers that are no longer progressing and continue the interrupted
   task with exact model `claude-sonnet-4-6`.
2. Keep the workers alive, wait for quota reset, and check both windows every 10 minutes.

The choice is recorded with `/antigravity:quota sonnet|wait`, `agy-quota --decision
sonnet|wait`, or the Codex `quota` MCP tool. The Sonnet route is permitted only after the
explicit choice. `agy-job cancel-all` cancels only plugin-managed background jobs; the
host also cancels any stalled tool tasks it started itself. Waiting uses the host's
scheduler/wakeup facility and resumes Gemini only after both windows are above 2%.

The tracker emits a one-time English notice when either window crosses 75%, 50%, 25%, or
10% remaining, such as `Agy Gemini 7d quota has only 50% remaining.` A threshold is not
announced again until that quota window resets above it.

## Permissions and troubleshooting

Write-capable tasks should run on a trusted branch with only the permissions you intend to grant. `--yolo` broadly exposes files, commands, network access, and process-visible credentials to the worker; it remains explicit unless enabled in plugin or environment settings.

If a call fails, run `/antigravity:setup` in Claude Code, the `doctor` MCP tool in Codex, or `agy-doctor` from Git Bash. More diagnostics are in [Troubleshooting](docs/TROUBLESHOOTING.md).

## License

[MIT](LICENSE). Third-party notices are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This is a community project and is not affiliated with Google, Anthropic, or OpenAI.

## Why Polyphony uses ConPTY on Windows

[ConPTY](https://learn.microsoft.com/en-us/windows/console/pseudoconsoles) is the Windows
pseudoconsole system developed and maintained by Microsoft. It provides a bidirectional,
UTF-8 terminal channel for console applications—the Windows counterpart to a Unix PTY.
Polyphony uses ConPTY because headless Antigravity sessions still expect real terminal
semantics; ordinary redirected pipes can lose output, stall permission/tool flows, or
misrepresent an active process as hung. The bundled bridge hosts `agy` inside a genuine
Windows pseudoconsole while preserving structured output, Unicode, timeouts, and exit
codes for Claude Code and Codex.
