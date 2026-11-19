# Codex MCP Memory

A Windows-first Codex skill for investigating growing MCP process sets, measuring memory, and safely reviewing completed chats for a **one-time runtime unload** without sacrificing history or active work.

**v0.1.0 is a partial mitigation toolkit, not a complete RAM fix.** It does not install an idle proxy, periodically archive chats, kill processes by name, change Codex configuration, or restart the application.

## Install

Download the `v0.1.0` release ZIP, extract it, review the scripts, then run in PowerShell:

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
- A JSONL history backup/verification helper that never restores or edits chat history.
- Acceptance criteria for separately maintained idle proxies, without shipping an unverified universal proxy.

Requirements: Codex with skills support; Windows PowerShell with CIM and Get-Process for snapshots; Python 3.10+ standard library for comparison/history helpers. Native chat-management tools are required for the optional unload. Without them, the skill stops at diagnosis. No new MCP server or background service is needed.

## Limits and safety

Native archive/unarchive is an observed workaround, not a documented unload API guarantee. A completed turn does not prove a browser, REPL, subscription or native document session is disposable. Status-check and archive are not atomic. Skip uncertain or active families, including new descendants. A protected chat remains protected throughout that pass even if it finishes later.

Private committed memory is not unique resident RAM. Summed working sets double-count shared pages. Snapshot output contains process metadata and should stay private; never commit snapshots, rollout backups, tokens, local configs or chat IDs. The bundled scripts do not terminate processes or invoke native chat mutations.

The initial release is tested on native Windows; it does not claim macOS/Linux lifecycle coverage. Helpers can be tested without real chat mutations. Installing a skill does not repair Codex's internal process lifetime management.

## Validation

```powershell
python -m unittest discover -s tests -v
```

Tests cover PID reuse, root replacement, cohort errors, history mutation detection, duplicate inputs and refusing unsafe history inputs. Run the bundled Codex skill validator when available, then test installation into a new temporary directory. The release records the exact tested source revision.

## Version plan

`0.1.0`: diagnostics and guarded recovery, with explicit unresolved RAM scope.

A later release can add validated lifecycle management only after repeated real-chat idle/wake cycles preserve history, active calls, stateful ownership and bounded memory. Do not label it a full RAM fix based only on a lower process count or one successful cleanup. Keep immutable tags and document regressions, remaining exclusions and rollback.

Русский запрос для Codex: «Используй $codex-mcp-memory: замерь память Codex и MCP, не трогай активные чаты, освободи только проверенные завершённые задачи и сохрани историю». Полное автоматическое решение RAM в этой версии не заявляется.

## License

MIT. This is a community project, not an official OpenAI component.
