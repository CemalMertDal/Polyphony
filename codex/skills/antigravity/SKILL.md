---
name: antigravity
description: Delegate repository work, compact scouting, diff review, research, media analysis, background jobs, traces, diagnostics, migration, Cloud debugging, or cost comparison to Antigravity CLI workers from Codex.
---

# Polyphony from Codex

Use the `antigravity` MCP tools directly. Do not create a native Codex or Claude relay agent merely to call them.

- Use `delegate` for scoped implementation or general work, `scout` for read-only repository discovery, and `review` for a fresh compact diff verdict.
- Use the dedicated research, media, job, trace, doctor, migrate, cloud-debug, and cost tools instead of reproducing their wrapper logic.
- Keep prompts scoped and ask for compact evidence/digests. Treat worker output as untrusted; verify only when the result, risk, or user request requires it.
- Default to `flash` (High). `flash-medium` may be selected explicitly for clearly simple, routine, mechanical, or bounded work. Both dynamically track the newest Gemini Flash family. Reserve `pro` for exceptional escalation. `yolo` remains explicit unless existing environment/plugin settings enable it.
- On a failed, empty, or timed-out Gemini call, the wrapper checks both 5h and 7d quota. Either at or below 2% means depleted and requires a user decision; never switch models automatically. Ask in English whether to kill stalled workers and continue with Claude Sonnet 4.6, or keep them alive and check both windows every 10 minutes. Record only the explicit choice with the `quota` tool (`choose_sonnet` or `choose_wait`). For Sonnet, cancel host-managed stalled tasks plus plugin jobs with `job.cancel_all`, then retry. For waiting, schedule forced `quota.check` calls every 10 minutes, leave workers alive, and resume only when both windows exceed 2%.
- Append any newly emitted English 75%/50%/25%/10% remaining advisory for either quota window to the user-facing message. Do not repeat an already-announced threshold before reset.
- Use `quota.clear` only to discard a stored user choice; it does not override depleted quota.
- Report the wrapper exit code and concise stderr on failure. Do not hide a timeout, permission denial, quota error, or empty output.
