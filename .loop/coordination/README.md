# Thread Coordination Records

These files are machine-readable operational snapshots for the Command Center, Thread A and Thread
B. They do not replace `.loop/progress.json`, acceptance records or Git history.

- `command-center.json`: dispatch authority and global synchronization state.
- `thread-a.json`: current Engineering Runtime checkout and gate.
- `thread-b.json`: current Persona Lab checkout and gate.

Only the assigned owner may update a thread envelope during an authorized mission. Any conflicting
snapshot must be resolved against Git, CI and the latest approved milestone.
