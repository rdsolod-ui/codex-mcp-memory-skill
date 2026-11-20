---
name: codex-mcp-memory
description: Diagnose Codex Desktop and local MCP memory growth, measure process cohorts, and safely review completed chats for a one-time runtime unload while preserving history and active work. Use for Codex RAM pressure or repeated MCP process sets, not general operating-system cleanup.
metadata:
  version: "0.2.1"
---

# Codex MCP memory

This is a Windows-first diagnostic and guarded recovery skill, not a complete RAM fix. Installation adds instructions, read-only helpers and an opt-in stdio proxy; it does not activate the proxy, change Codex settings, or start a watcher.

## Establish the boundary

- Identify the actual host, Codex Desktop/backend executable, process creation times, configuration scope and affected MCP owner. Do not infer a Windows process belongs to a chat from its name or low CPU alone. Do not start WSL for a native Windows consumer.
- Discover the available native chat tools. List chats and read the current turn before selecting anything. Build a fixed protected set containing this chat, all active/waiting chats, their descendants and uncertain state owners. If a protected task completes later, it remains protected for this pass.
- Check the whole target family, including newly created descendants; an old list of three children is not proof that there are still only three. `notLoaded` needs no further unloading. `idle` alone is insufficient: examine the latest turn, pending commands, tools, child tasks and stateful sessions.
- Existing task authorization applies. A request to measure is not permission to unload. A request to safely free completed chats permits the bounded procedure below when all eligibility checks pass; do not add redundant confirmation gates.

## Measure before acting

On Windows, identify the Desktop root PID from live executable/parent evidence, then run:

```powershell
& '<skill-path>/scripts/snapshot.ps1' -RootPid <verified-pid> -OutputPath '<private-evidence-dir>/before.json'
```

The evidence directory must already exist outside a public repository. A snapshot contains PID, creation time, parent, executable name and memory counters, but no command lines or environment values. Pattern-based MCP classification is provisional, not a chat-to-process ownership map. Unknown descendants stay separate; classify them read-only if needed, without printing credentials from arguments.

Report private committed bytes separately from the sum of working sets. Working sets share pages and cannot be summed into unique physical RAM. Also report system free physical memory, sampling races and excluded/uncertain processes. The diagnostic command itself may appear among other descendants.

For a natural idle/unload observation, read [native-retention.md](references/native-retention.md). A completed turn and an inactive UI view are different conditions; do not start an owner-retention timer from turn completion alone. Keep observation bounded and report an interrupted interval as incomplete.

## One-time release of eligible completed chats

Read [completed-chat-unload.md](references/completed-chat-unload.md) and [history-formats.md](references/history-formats.md) before any mutation. A rollout JSONL backup alone is insufficient for paginated history. Use the native mechanism only when it is available and has been verified for the current Desktop version. Preserve history and metadata, recheck immediately before each action, and restore visibility immediately after archive even if a later step fails. Never automate periodic archiving.

If the family is active or owns uncertain state, skip it. Do not kill its MCP processes, wait for it to become eligible and silently act later, interrupt it, or tell another chat to stop. If nothing qualifies, report **zero action-attributed savings**. Natural memory fluctuations are not cleanup savings.

After the action, take a new snapshot and compare an independently verified cohort:

```text
python <skill-path>/scripts/compare.py before.json after.json --cohort cohort.json --output comparison.json
```

The cohort is an array of `{ "pid": ..., "createdUtc": "..." }` from the before snapshot. A missing row alone is not proof of termination: confirm the same identity is absent in a fresh OS query, and separate unrelated exits/new processes. Without a cohort the script reports general churn only, not causal savings.

## Recurring idle behavior

Read [idle-proxy-contract.md](references/idle-proxy-contract.md) and [proxy-setup.md](references/proxy-setup.md) before using the opt-in proxy. Diagnose live child processes separately from parked proxy connections and old unwrapped launches. For reviewed stateless or durable-state servers use `idle`. For a reviewed server that creates no user state during discovery, `until-first-use` may release an unused catalog-only process; the first non-catalog operation permanently pins it. Existing browser/REPL sessions, jobs and unreviewed bindings stay protected. Never apply a profile solely by server name, and never replace live active connections to roll out new code.

## Finish with evidence

State memory totals, eligible/skipped families, actual actions, PID-plus-creation-time savings, history verification, active-work preservation and unresolved limits. Distinguish saved configuration, installation, discovery, real tool execution and cold-start/OS-boot verification. Do not restart Codex just to load a skill or claim global RAM pressure is solved by unloading one family.
