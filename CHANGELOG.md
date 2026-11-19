# Changelog

## 0.2.0 - 2026-11-19

- Ship an opt-in stdio lifecycle proxy, with private reviewed profiles rather than a universal allowlist.
- Add `until-first-use`: release an unused catalog-only server; pin it before any working operation to preserve in-memory state.
- Answer negotiated health pings locally so they cannot prevent idle shutdown.
- Preserve the delayed-exit fix: retain the owned process handle until confirmed exit, queue unsent requests, and never replay ambiguous calls.
- Pin unknown state, changed reviewed sources, subscriptions, reverse requests and task state. Add protocol and state-preservation tests.
- Document that live active connections retain their old launchers, parked proxies consume some memory, and GPU VRAM cannot replace ordinary CPU process memory.

This is a bounded mitigation release. It does not claim automatic unloading of all Desktop chat runtimes or a complete RAM fix.


## 0.1.0 — 2026-11-19

- Initial installable Codex skill for Windows memory diagnosis and guarded one-time recovery.
- Read-only process snapshots, identity-aware comparisons and rollout backup verification.
- Protected active-chat families, explicit stateful exclusions and immediate visibility restoration requirements.
- No automatic idle proxy or complete RAM fix in this release.
