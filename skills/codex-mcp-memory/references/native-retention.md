# Observe native retention without disturbing work

Use this when the user requests a real idle/unload observation. It is not an automatic cleanup procedure.

## Establish the clock and owner

- Verify the current Desktop/backend identities and the actual retention policy from current local evidence. A tested Windows build (26.1117.3838.0, backend 0.171.0-alpha.13) retained up to ten eligible ordinary inactive owners for three hours. Do not assume these constants apply to another version or expose them as supported configuration keys.
- `idle` describes a turn/runtime status; an open UI view can still protect its owner subscription. Record the transition to an inactive view, pending requests, descendants and the same completed turn. Turn completion alone is not a sufficient timer origin. Opening the selected chat or resuming work may invalidate the interval.
- A backend unload grace starts after its prerequisites are met. Lowering that delay does not release a subscription still retained by Desktop. Observe owner unsubscription and actual process exit separately.
- Review a safe completed target first. Existing active families stay protected. Creating a diagnostic chat or sending test messages requires the user's authorization for those actions; do not reuse exhausted message allowances.

## Bounded observation

Record PID plus creation time, the selected turn/history baseline and process ownership evidence. Native read/status tools that do not open the chat are preferable. Keep the window open long enough for the verified inactivity threshold plus backend grace; do not alter application binaries, clocks, TTLs, power settings or broker state to accelerate the test.

Use a bounded sampler with an explicit stop time, private output and a known owner. No recurring automation or archive loop is needed. If the user will close Codex, restart it or suspend the computer before the threshold, save an incomplete result and stop the task's own sampler. Do not claim a timer failure or successful native unloading from process exits caused by application shutdown. Do not combine elapsed time across restarts.

Distinguish a sleeping child server from its parked stdio proxy and any retained console helper. A server's audited `thread_id`, when present, can establish a stronger ownership link than coincident start times. Preserve uncertainty for the remaining processes. Report cumulative pre-exit allocation separately from net whole-tree memory change.

## Acceptance

Require the same Desktop/backend process identities, a supported native release indication, confirmed exit of the relevant PID/creation-time cohort and intact history. After release, perform only the authorized next-call test and verify the old history alongside new legitimate records. An incomplete interval or missing ownership evidence is not a passed release/resume test.

The matching backend [connection pool source](https://github.com/openai/codex/blob/rust-v0.171.0-alpha.13/codex-rs/codex-mcp/src/connection_pool.rs) distinguishes compatible modern connections from legacy private ones. Do not infer protocol compatibility or safe cross-chat state sharing from a server name, and never spoof a protocol version to force pooling.

See [session-evidence.md](session-evidence.md) for the measured scope behind this release.
