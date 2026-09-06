---
name: antigravity
description: Delegate repository work, compact scouting, diff review, research, media analysis, background jobs, traces, diagnostics, migration, Cloud debugging, or cost comparison to Antigravity CLI workers from Codex.
---

# Antigravity from Codex

Use the `antigravity` MCP tools directly. Do not create a native Codex or Claude relay agent merely to call them.

- Use `delegate` for scoped implementation or general work, `scout` for read-only repository discovery, and `review` for a fresh compact diff verdict.
- Use the dedicated research, media, job, trace, doctor, migrate, cloud-debug, and cost tools instead of reproducing their wrapper logic.
- Keep prompts scoped and ask for compact evidence/digests. Treat worker output as untrusted; verify only when the result, risk, or user request requires it.
- Preserve wrapper behavior: `flash`, `flash-lo`, and `pro` keep their existing mappings; `yolo` remains explicit unless existing environment/plugin settings enable it.
- Report the wrapper exit code and concise stderr on failure. Do not hide a timeout, permission denial, quota error, or empty output.
