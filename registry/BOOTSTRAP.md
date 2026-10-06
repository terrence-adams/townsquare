# Registry bootstrap boundary

Registry owns a separate SQLite database and schema; it never shares the Ledger
database, migrations table, foreign keys, or transaction. `registry-migrate` is
the sole Registry schema writer. It takes a create-exclusive filesystem lock;
the runtime only verifies schema/audit-contract compatibility and performs no DDL.

The Ledger `migrate` service remains the sole Ledger migrator and Ledger starts
only after it succeeds. `registry-migrate` is the sole Registry migrator and
Registry starts only after it succeeds. Do not run two Registry schema writers,
and do not combine the independent databases into a cross-service transaction.
