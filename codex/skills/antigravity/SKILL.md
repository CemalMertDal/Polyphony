---
name: antigravity
description: Delegate repository work, compact scouting, diff review, research, media analysis, background jobs, traces, diagnostics, migration, Cloud debugging, or cost comparison to Antigravity CLI workers from Codex.
---

# Antigravity from Codex

Use the `antigravity` MCP tools directly. Do not create a native Codex or Claude relay agent merely to call them.

- Use `delegate` for scoped implementation or general work, `scout` for read-only repository discovery, and `review` for a fresh compact diff verdict.
- Use the dedicated research, media, job, trace, doctor, migrate, cloud-debug, and cost tools instead of reproducing their wrapper logic.
- Keep prompts scoped and ask for compact evidence/digests. Treat worker output as untrusted; verify only when the result, risk, or user request requires it.
- Deliberately choose `flash-medium` for simple, routine, mechanical, or bounded work; choose `flash` (High) for complex reasoning, architecture, concurrency/security, ambiguous multi-file behavior, difficult debugging, adversarial review, or one materially incomplete Medium result. Both dynamically track the newest Gemini Flash family. Reserve `pro` for exceptional escalation.
- Never default every call to High. `yolo` remains explicit unless existing environment/plugin settings enable it.
- A Gemini Flash quota automatically retries the same task once with `claude-sonnet-4-6`; the retry starts a fresh model conversation, preserves wrapper settings, and never chains another fallback.
- Report the wrapper exit code and concise stderr on failure. Do not hide a timeout, permission denial, quota error, or empty output.
