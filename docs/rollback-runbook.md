# Rollback boundary

Before the first native write, rollback means stop the Compose project and restart
the prior digest only after preserving the release manifest, logs, and migration
evidence. Never use mutable tags.

After a native write, do **not** roll the ledger database backward or restore an
older backup over it. Preserve the database, append a corrective ledger event, and
escalate for a data/release decision. A separate restore drill may prove a backup
in an empty directory; it is not permission to overwrite live state.

Migration failure leaves the stack stopped. Capture its logs and database copy,
then use a reviewed forward repair. No automatic destructive rollback exists.
