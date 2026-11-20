# Evidence and limits for 0.2.1

Observed on native Windows Desktop 26.1117.3838.0 / backend 0.171.0-alpha.13 on 2026-11-20. These are single-host observations, not performance promises or acceptance of every integration.

- A 30.5-minute ordinary-work observation recorded 15 automatic child-server stops. All recorded server exits were 0; the longest shutdown was 1,935 ms. The full terminated trees contained 33 processes with 786.23 MiB summed from their last pre-exit samples. This is cumulative lifecycle accounting, not simultaneous physical RAM savings.
- Parked proxies still held client connections. Their count grew from 21 to 35 in that window, then a later snapshot showed 31. This does not demonstrate strictly monotonic or unlimited accumulation. Active work affected total memory throughout the session.
- A separate authorized diagnostic read established direct ownership of one Filesystem proxy through its audit thread identifier. Its child tree stopped after the configured idle period: exit 0, 120 ms, 67.11 MiB in the last pre-stop sample. The proxy remained at about 14.26 MiB plus a 1.14 MiB console helper.
- The native retention observation collected 145 periodic process snapshots, but only 124.28 minutes after a confirmed inactive-view transition. The user planned to shut down before the three-hour threshold. The sampler was stopped; **native three-hour release and the next read after that release were not tested**.
- Selected rollout prefixes, paginated turn/item rows and native metadata were preserved. The original two turns/eight items survived a legitimate third diagnostic turn; the post-read baseline stayed unchanged during observation. No working chat was archived or interrupted, and Desktop/backend identities remained unchanged.

This release improves history safeguards and diagnostic interpretation. The lifecycle proxy code is unchanged from 0.2.0. Earlier sleep/wake checks remain earlier evidence; they are not a new native retention acceptance test. Public upstream context: [owner-side release request](https://github.com/openai/codex/issues/56512#issuecomment-7040231928).

Private chat IDs, local paths, raw history, snapshots, configurations and credentials are deliberately excluded from this package. A complete solution to Desktop RAM retention is not claimed.
