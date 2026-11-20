# Codex MCP Memory

A Windows-first Codex skill for investigating growing MCP process sets, measuring memory, and safely reviewing completed chats for a **one-time runtime unload** without sacrificing history or active work.

**v0.2.1 adds current-history safeguards and evidence-based native retention checks.** The opt-in proxy from v0.2.0 can release reviewed unused servers while preserving the client connection. This package does not fix every source of Desktop RAM growth, automatically change configuration, periodically archive chats, kill processes by name, or restart the application.

## Install

Download the `v0.2.1` release ZIP, extract it, review the scripts, then run in PowerShell:

```powershell
./install.ps1
```

The default destination is `$env:CODEX_HOME/skills/codex-mcp-memory`, or `$env:USERPROFILE/.codex/skills/codex-mcp-memory` when CODEX_HOME is unset. Existing folders are never overwritten. For an isolated installation check:

```powershell
./install.ps1 -Destination 'C:/YourPrivateTestFolder/codex-mcp-memory'
```

Alternatively, ask Codex's skill installer to install the `skills/codex-mcp-memory` directory from this repository. Installation is only file placement; discovery in an already-open chat is a separate check. Do not restart active work merely to load it.

Invoke it in Codex:

```text
Use $codex-mcp-memory to measure Codex and MCP memory. Only release
verified completed chats; preserve active tasks and history.
```

## What is included

- A focused skill with a protected-chat policy and a guarded native archive → immediate unarchive procedure, conditional on verified Desktop behavior.
- A read-only Windows process-tree snapshot with PID/creation-time identity and explicit uncertainty in MCP classification.
- A Python snapshot comparison helper. It separates exited identities from overall memory churn; it cannot establish ownership or causal savings by itself.
- A JSONL history backup/verification helper with strict verification by default and explicit prefix verification after a legitimate appended turn. It never restores or edits history and is not a SQLite backup tool.
- Guardrails for paginated history and a bounded native-retention observation that accounts for active UI views, application shutdown and incomplete test windows.
- An opt-in stdio proxy with `idle`, `until-first-use` and `pinned` modes, reviewed-source guards, serialized shutdown/wake and no mutation replay. Host-specific profiles are deliberately not included.

Requirements: Codex with skills support; Windows PowerShell with CIM and Get-Process for snapshots; Python 3.10+ standard library for comparison/history helpers. Native chat-management tools are required for the optional unload. Without them, the skill stops at diagnosis. No new MCP server or background service is needed.

## Limits and safety

Native archive/unarchive is an observed workaround, not a documented unload API guarantee. A completed turn does not prove a browser, REPL, subscription or native document session is disposable. Status-check and archive are not atomic. Skip uncertain or active families, including new descendants. A protected chat remains protected throughout that pass even if it finishes later.

Private committed memory is not unique resident RAM. Summed working sets double-count shared pages. Snapshot output contains process metadata and should stay private; never commit snapshots, rollout backups, tokens, local configs or chat IDs. The snapshot/comparison/history helpers do not terminate processes. The opt-in proxy stops only its directly owned reviewed child under the selected lifecycle contract. No script invokes native chat mutations.

The initial release is tested on native Windows; it does not claim macOS/Linux lifecycle coverage. Helpers can be tested without real chat mutations. Installing a skill does not repair Codex's internal process lifetime management.

## Validation

```powershell
python -m unittest discover -s tests -v
```

Tests cover PID reuse, root replacement, cohort errors, history mutation/truncation detection, preserved UTF-8 prefixes after append, duplicate inputs, protocol sleep/wake, first-use state preservation, pending calls, health pings, source changes, process failure and EOF cleanup. Run the bundled Codex skill validator when available, then test installation into a new temporary directory. The release records the exact tested source revision.

## Lifecycle setup

Ask Codex to read [proxy setup](skills/codex-mcp-memory/references/proxy-setup.md), inspect your actual MCP sources and produce a private reviewed profile. Reuse the current runtimes. Installation alone does not activate lifecycle management.

`idle` is for verified durable/reconstructible state. `until-first-use` addresses the unused-server gap: a reviewed server may sleep while only initialization and catalog operations occurred, but becomes permanently pinned **before the first working call**. It never resets an already-used browser or reasoning chain. Health pings do not keep an unused child alive.

New settings apply to new connections. Already-running active chats retain their current processes. Existing inactive chats require individual eligibility/history checks; there is no safe universal background sweeper in this package. Parked stdio proxies themselves retain a small amount of memory.

## Version history and remaining scope

`0.1.0`: diagnostics and guarded recovery, with explicit unresolved RAM scope.

`0.2.0`: opt-in lifecycle proxy, unused catalog-only stateful-server mode, heartbeat fix and protocol tests. Native session unloading, already-used stateful integrations and Desktop/backend memory remain outside automatic management. Real local server tests and isolated protocol tests are distinct from applying the new code in every existing chat. See release notes for actual validation scope.

`0.2.1`: paginated-history safeguards, explicit JSONL prefix verification and bounded native-retention checks. The proxy is unchanged. The real three-hour Desktop release/resume test remains incomplete; see [sanitized session evidence](skills/codex-mcp-memory/references/session-evidence.md).

Русский запрос для Codex: «Используй $codex-mcp-memory: замерь память Codex и MCP, не трогай активные чаты, освободи только проверенные завершённые задачи и сохрани историю». Полное автоматическое решение RAM в этой версии не заявляется.

## License

MIT. This is a community project, not an official OpenAI component.
