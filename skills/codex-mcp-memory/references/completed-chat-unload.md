# Guarded one-time unload

This is a recovery workaround observed in Codex Desktop, not a stable lifecycle API guarantee. Native archive/unarchive may release a chat's local runtime while retaining its history. It is not atomic with checking chat status. Do not use it when concurrency or ownership cannot be resolved, and do not install an archive loop.

## Eligibility and backup

1. Freeze the protected set for this pass: current, active, approval/input-waiting chats, their descendants, and uncertain state owners. A busy parent protects its entire family.
2. Read current native status, exact last turn ID/status and descendants. Only select explicitly scoped, completed, idle chats without pending tool/terminal jobs or needed memory-only state. Skip already `notLoaded` chats. Review browser/REPL/app bindings even if their user-facing turn has finished.
3. Record native IDs, host, title, project/sidebar placement, pin/archive state, latest completed turn, and child relationships in a private evidence receipt. Find the exact rollout file paths through the existing local index/schema read-only; do not guess them. Do not copy a live SQLite file with its WAL using ordinary file copy, and never edit the database to unload a chat.
4. Back up selected rollout bytes with `scripts/history_guard.py backup --output <new-private-backup-dir> <explicit.jsonl> ...`. Its parent directory must exist. The helper refuses existing output, non-JSONL inputs and changes observed during copying. Keep the receipt and metadata outside the repository. It proves file bytes, not native metadata or a consistent database transaction.

## Native action and recovery

- Discover the native `read_thread` and `set_thread_archived` equivalents and their current schemas. Never hardcode a broker pipe, internal token, application-binary patch or SQL mutation as a substitute.
- Process eligible descendants first. Immediately before **each** archive, recheck the same completed turn, idle status, descendants and protected set. Skip on any change. If the check/action race is materially unresolved, do not act.
- Invoke native archive once, then immediate unarchive in a `finally` recovery path. Keep the exact host/ID explicit. Do not leave a chat archived because a memory measurement or unrelated verification failed. On uncertain archive outcome, inspect native state; restore visibility through the native API, not history replacement.
- Read back the same chat ID, title/project/pin/sidebar state, last completed turn, child relationships and rollout bytes. `history_guard.py verify <receipt.json>` exits nonzero if any selected file changed. If a legitimate new turn appeared, preserve it and investigate; never overwrite new history with the backup.
- Verify the released process identities and the protected processes. If the result remains loaded or differs from expected history/metadata, report failure at that layer and stop further unloads. Do not escalate into process killing.

## Interpretation

`notLoaded` means the old runtime is no longer resident; it does not prove every possible tool can reconstruct its previous memory. Retain a verified next-call test only for an explicitly authorized diagnostic chat/tool. Sending a message to another chat is a separate action and must be authorized. Never wake every MCP just to mark the configuration “applied.”

If native management tools, a recoverable history backup or current-version behavior are unavailable, provide the memory diagnosis and explain the blocked unload. Do not restart Codex, change hosts, or claim a successful release from file edits alone.
