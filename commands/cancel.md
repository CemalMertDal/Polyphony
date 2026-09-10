---
description: Cancel a running background Antigravity (agy) delegation job.
argument-hint: "<job-id|--all>"
---

Cancel a running background agy job.

Run `agy-job cancel <job-id>`. For `--all`, run `agy-job cancel-all`; this targets only
jobs started through the plugin job registry, not arbitrary `agy.exe` processes.

Confirm to the user whether it was cancelled or had already finished.
