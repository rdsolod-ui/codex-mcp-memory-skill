# Opt-in lifecycle proxy

The script `scripts/idle_proxy.py` is a stdio intermediary, not a background sweeper. It keeps the client's connection alive while stopping only its own reviewed server process. There is no automatic configuration discovery, universal safe-server list, or chat archive loop.

## Diagnose the remaining sets first

Separate live MCP children, sleeping proxies (a small process must retain each stdio pipe), old direct launches, stateful sessions, and native app/backend memory. A lower child count does not mean the whole chat was unloaded. New child tasks may legitimately create their own MCP connections. Inspect the current turn and actual process identities before attributing a set to abandoned work.

An app-server protocol can expose `thread/unsubscribe` without giving this agent authority over the Desktop's existing connection subscription. A second connection is not that subscription. Do not manipulate private broker state or patch application binaries to force unloading.

## Choose a reviewed mode

| Mode | When it may sleep | Required evidence |
| --- | --- | --- |
| `pinned` (default) | Never | Safe fallback; forwards traffic |
| `idle` | After completed work and idle timeout | Every needed state is durable or reconstructible; exact server code reviewed |
| `until-first-use` | Only before first non-catalog operation | Initialization and catalog requests create no needed user state; wake handshake/catalog tested |

`until-first-use` permanently pins the connection before forwarding `tools/call`, `resources/read`, `prompts/get`, or an unknown operation, even if that call later fails or is cancelled. It is suitable only for a reviewed startup contract, not for resetting an already-used browser or reasoning server. There is no reset/unpin command.

Source fingerprint changes, unsupported capabilities, subscriptions/list changes, reverse requests, tasks and unknown stateful notifications conservatively pin the process. A client `ping` is answered by the proxy after negotiation and does not extend idle time or wake a server. Catalog queries can wake it and refresh the idle timer; their semantics are not cached.

## Prepare a private profile

Reuse the existing Python and server runtime. Launch a directly owned server executable with a structured argument array; avoid shell/npx wrappers and servers with unreviewed child-process trees. Review relevant source dependencies, initialization, shutdown, data paths and actual protocol version. Hash the reviewed source, not merely its launcher. Hashing unreviewed code is not an audit.

Example **shape**, requiring real values from the current host:

```json
{
  "reviewed-server": {
    "command": ["<absolute-runtime-path>", "<absolute-server-entrypoint>"],
    "lifecycle": "until-first-use",
    "allowed_capabilities": ["tools"],
    "fingerprints": {"<reviewed-source-path>": "<sha256>"},
    "audit_dir": "<private-bounded-log-directory>"
  }
}
```

Use a private JSON file outside the repository. Never copy credentials, local profiles, chat IDs or user data into a public release. `env_defaults` may supply reviewed non-secret data-path defaults only when an inherited value is missing. Do not replace a missing durable database with an empty one.

```text
python <skill-path>/scripts/idle_proxy.py --profiles-file <private-profiles.json> --profile reviewed-server --idle-seconds 180
```

Missing lifecycle defaults to pinned. Sleep-enabled CLI profiles require fingerprints. Profile names accept letters, digits, underscore and hyphen only. The timeout range is 1–3600 seconds; use shortened values only for isolated tests.

## Acceptance and activation

Before changing real startup configuration:

1. Test the current protocol negotiation, catalog, repeated sleep/wake, PID exit and replacement through the same stdio connection. For durable servers, write only task-owned data and read it after waking. Verify no child overlap or orphan after EOF.
2. For pre-use mode, test repeated catalog-only cycles, then a successful first operation and a second operation after the timeout: same server PID and preserved state. Browser tests must use their own isolated browser, never close a user's shared context.
3. Exercise pending calls, cancellation during shutdown, delayed exit acknowledgment, startup failure, unexpected process exit, and no automatic mutation replay. Keep production-timeout and shortened-timeout evidence separate.
4. Back up the exact launcher/config/profile files, compare current bytes before writing, change only the reviewed entries and read back. Never expand roots, alter global environment, replace native runtime settings or disable unrelated integrations.

Changing the file affects future proxy processes. Existing active direct/proxy connections keep their current code and must not be killed for rollout. Only use the separately documented guarded procedure for independently eligible completed chats. If no native hot replacement exists, state that limitation; do not claim all open chats were upgraded.

Rollback uses the backed-up exact files with a concurrent-change check. It controls future launches too; do not restart active work to roll back a saved launcher. Keep the existing client EOF behavior and preserve chat history. A successful isolated test is not evidence of discovery or use in every Desktop chat.

## RAM and GPU

The proxy reduces retained server processes; it cannot relocate ordinary Python/Node/Electron heaps into video memory. GPU memory requires application-specific GPU allocations. Integrated GPUs commonly share system RAM and do not provide an independent spare RAM pool. Report private committed bytes and physical availability separately.
