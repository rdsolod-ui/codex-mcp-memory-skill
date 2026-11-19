---
name: codex-mcp-memory
description: Diagnose Codex Desktop and local MCP memory growth, measure process cohorts, and safely review completed chats for a one-time runtime unload while preserving history and active work. Use for Codex RAM pressure or repeated MCP process sets, not general operating-system cleanup.
metadata:
  version: "0.1.0"
---

# Codex MCP memory

This is a Windows-first diagnostic and guarded recovery skill, not a complete RAM fix. Installation adds instructions and read-only helpers; it does not change Codex settings, install an idle proxy, or start a watcher.

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

## One-time release of eligible completed chats

Read [completed-chat-unload.md](references/completed-chat-unload.md) before any mutation. Use the native mechanism only when it is available and has been verified for the current Desktop version. Preserve history and metadata, recheck immediately before each action, and restore visibility immediately after archive even if a later step fails. Never automate periodic archiving.

If the family is active or owns uncertain state, skip it. Do not kill its MCP processes, wait for it to become eligible and silently act later, interrupt it, or tell another chat to stop. If nothing qualifies, report **zero action-attributed savings**. Natural memory fluctuations are not cleanup savings.

After the action, take a new snapshot and compare an independently verified cohort:

```text
python <skill-path>/scripts/compare.py before.json after.json --cohort cohort.json --output comparison.json
```

The cohort is an array of `{ "pid": ..., "createdUtc": "..." }` from the before snapshot. A missing row alone is not proof of termination: confirm the same identity is absent in a fresh OS query, and separate unrelated exits/new processes. Without a cohort the script reports general churn only, not causal savings.

## Recurring idle behavior

Read [idle-proxy-contract.md](references/idle-proxy-contract.md) only when analyzing or adapting an existing idle proxy. v0.1.0 does not ship or install a proxy. Never turn a previously validated local profile into a universal allowlist. REPLs, browsers, in-memory jobs, subscriptions and native-app bindings remain protected unless restoration is demonstrated for that exact contract.

## Finish with evidence

State memory totals, eligible/skipped families, actual actions, PID-plus-creation-time savings, history verification, active-work preservation and unresolved limits. Distinguish saved configuration, installation, discovery, real tool execution and cold-start/OS-boot verification. Do not restart Codex just to load a skill or claim global RAM pressure is solved by unloading one family.
