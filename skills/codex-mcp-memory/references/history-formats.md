# History format and continuity

Read this before a one-time native unload, especially after a Desktop update. A previous release's rollout-only backup is not evidence of completeness for a newer storage format.

1. Read the actual selected chat's metadata and current database schema. Establish whether history is rollout-based, paginated, or another format. Locate authoritative files through the existing index; do not guess paths or launch another app-server against the live home to discover them.
2. Preserve the native identity, host, project/sidebar/pin/archive metadata, latest completed turn and descendant relationships. Back up only the selected chats to a private directory outside Git.
3. For paginated history, use a read-only SQLite URI (`mode=ro`) and an explicit read transaction. Inspect table columns and primary keys first, select rows by exact chat IDs, and close the connection in `finally`. Keep schema/selection details, deterministic row order and hashes with the backup. Never copy live SQLite/WAL files with ordinary file copy or write SQL to unload a chat.
4. In one tested Windows build, relevant tables were `thread_turns`, `thread_items`, `thread_history_projection_state` and `thread_realtime_items`. These names are evidence from that build, not a permanent schema or an exhaustive list for future releases. Include the current authoritative records and rollout bytes. If the schema or completeness is uncertain, stop at diagnosis.
5. Capture each store consistently, then re-read the selected history and metadata to check that they did not change across captures. Separate SQLite transactions and filesystem reads are not one atomic transaction. Recheck native activity immediately before any allowed mutation; an unresolved race excludes the chat.

## Read-back

With no new turn, compare selected records, rollout bytes and native metadata exactly. A path representation change must be resolved to the same actual file rather than mistaken for data movement.

If a legitimate new turn was independently confirmed, preserve it. Match old database rows by their actual primary keys and verify their contents are unchanged; report new rows separately. Mutable projection metadata may legitimately advance, but its change must be understood. Compare the original JSONL byte prefix rather than requiring the whole file to keep its old length. The existing helper supports:

```text
python scripts/history_guard.py verify <private-receipt.json> --allow-append
```

This option verifies an intact backup and unchanged source prefix, including UTF-8 bytes. It rejects truncation or modification of old bytes. It does not validate new content, a database, native state, or permission to unload. Strict whole-file verification remains the default. Never restore an old snapshot over newer work; neither helper mode writes history.

After an update, verify file installation, skill discovery, native tool execution and actual history continuity separately. A saved instruction does not change every open chat.
