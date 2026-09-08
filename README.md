<div align="center">

# 🛰️ Antigravity for Claude Code and Codex

**Use the Antigravity CLI (Gemini) as a collaborating worker from Claude Code or Codex.**

![Antigravity for Claude Code and Codex — Claude or Codex directs, Gemini executes](docs/hero.png)

Claude or Codex directs the work; Gemini handles the delegated execution.

</div>

---

## Overview

This plugin gives Claude Code and Codex the same Antigravity (`agy`) worker toolkit:

- scoped implementation and general delegation
- read-only repository scouting and independent diff review
- web research and media analysis
- background jobs, traces, diagnostics, migration, Cloud debugging, and cost comparison
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
/plugin marketplace add GryAsl/antigravity-for-claude-code-and-codex
/plugin install antigravity@antigravity-for-claude-code-and-codex
/antigravity:setup
```

The plugin installs its slash commands, Antigravity skill, custom agent, wrappers, and optional delegation-reminder hooks.

## Install for Codex

```powershell
codex plugin marketplace add https://github.com/GryAsl/antigravity-for-claude-code-and-codex
codex plugin add antigravity@antigravity-for-claude-code-and-codex
```

Start a new Codex task after installation. Codex receives direct MCP tools for delegation, scouting, review, research, media, jobs, traces, diagnostics, migration, Cloud debugging, and cost comparison. Review and trust the optional non-blocking hooks from `/hooks`; Codex does not trust plugin hooks automatically.

## Model routing

The caller should choose the tier that matches the task:

| Tier | Use it for | Model selection |
| --- | --- | --- |
| `flash-medium` | Simple, routine, mechanical, or tightly bounded work | Newest available Gemini Flash, Medium effort |
| `flash` | Complex reasoning, architecture, concurrency/security, difficult debugging, ambiguous multi-file work, or adversarial review | Newest available Gemini Flash, High effort |
| `pro` | Exceptional escalation only | Configured Gemini Pro model |

There is no Low tier. Both Flash tiers query `agy models` and automatically follow the newest available Gemini Flash family. If discovery is unavailable, version 0.28.0 falls back to Gemini 3.8 Flash at the selected effort level. Exact models can still be supplied with `--model` or the plugin configuration overrides.

## Usage

Claude Code examples:

```text
/antigravity:delegate --tier flash-medium "Add the missing unit tests"
/antigravity:delegate --tier flash "Diagnose this cross-module concurrency bug"
/antigravity:review
/antigravity:research "Research this topic and include source URLs"
```

Codex uses the corresponding `antigravity` MCP tools directly. The MCP adapter calls the same wrappers and returns their stdout, stderr, and exact exit code.

The wrappers are also available from Git Bash:

```text
agy-delegate --tier flash-medium --dir "C:\path\to\repo" --digest "Implement this bounded change"
agy-scout --tier flash-medium --dir "C:\path\to\repo" "Trace the request flow"
agy-review --tier flash --dir "C:\path\to\repo" --staged --goal "Implement feature X"
agy-job start --tier flash --dir "C:\path\to\repo" "Complete this long-running task"
```

Routine calls default to 30 minutes. The Codex MCP transport allows 35 minutes so a healthy long-running worker can return before the transport closes. Use `--timeout` when a task needs a different wrapper deadline.

## Permissions and troubleshooting

Write-capable tasks should run on a trusted branch with only the permissions you intend to grant. `--yolo` broadly exposes files, commands, network access, and process-visible credentials to the worker; it remains explicit unless enabled in plugin or environment settings.

If a call fails, run `/antigravity:setup` in Claude Code, the `doctor` MCP tool in Codex, or `agy-doctor` from Git Bash. More diagnostics are in [Troubleshooting](docs/TROUBLESHOOTING.md).

## License

[MIT](LICENSE). Third-party notices are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This is a community project and is not affiliated with Google, Anthropic, or OpenAI.
