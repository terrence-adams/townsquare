# Encrypted backup and restore contract

Backups are two independent consistency domains: `ledger.db` and `registry.db`.
They are never represented as one atomic cross-service snapshot or watermark.
`create-backup.py` uses SQLite's online backup API, fsyncs each closed copy,
records plaintext and ciphertext hashes plus integrity/FK checks and row counts,
then encrypts with `age`. It emits an unsigned canonical checkpoint request.
The NAS never receives a signing private key. A separate operator environment
uses `operator-sign-checkpoint.py`; NAS retains only the signature and public
verification material. Plaintext staging is removed on normal completion.

The operator independently publishes the signed checkpoint to the approved
external journal. This package contains no journal credential or automatic egress.

Run `restore-drill.py` only against a newly created empty drill directory. It
verifies manifest signatures and ciphertext hashes before decryption, runs
`PRAGMA integrity_check`, and never replaces a live database. Retention deletion
is a separately reviewed operator action; `prune.py` supports a dry run by
default and refuses paths outside the configured backup root.
