# Optional idle proxy analysis

This reference describes acceptance criteria for an existing or separately requested proxy. No proxy is installed by this skill. A small process count is not the goal if it destroys active state.

An eligible stdio proxy must retain the client connection and stop only its own child after an explicit idle policy with no outstanding client or reverse requests. An idle CPU is not evidence of inactivity. State must live in a verified durable file/service or be reconstructible from the complete request and initialization contract.

Check legacy `initialize`/`notifications/initialized`, discovery fallback and handshake-free protocols separately. Replay only the validated startup contract on a new child. Never replay an ambiguously completed mutating request. Subscriptions, dynamic roots, tasks and unknown stateful operations block idle shutdown until their semantics are demonstrated.

Serialize queue admission with shutdown. Close stdin first, wait boundedly for EOF, then terminate only a retained, identity-checked owned process handle if required. Wait for confirmed exit before launching a replacement or accepting child-bound work. On Windows, verify descendant cleanup and windowless helper launch independently; do not apply console-helper launch recipes to packaged Desktop applications.

Preserve app-managed primary runtime, node_repl, broker/pipe ownership, existing browser profiles and host-specific runtime paths. Do not enable sleeping for a browser, REPL, native document binding or in-memory job based only on state being visible elsewhere.

Acceptance requires real before/after calls over the same client connection, repeated idle/wake cycles, long in-flight requests, EOF, a child that delays termination, PID reuse, failed initialization, ambiguous writes and relevant subscriptions. Compare PID plus creation time and the complete owned subtree. Test configuration saving, fresh startup and existing-chat application separately.

Diagnostics must be bounded and omit request contents, credentials and environment dumps. Keep scoped backups and a reversible per-profile change. Avoid global PATH/backend/security changes, blanket MCP disablement, or introducing a duplicate watcher. Publish tested limitations; a local success does not establish portability to every MCP or OS.
