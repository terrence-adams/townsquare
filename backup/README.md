# Encrypted backup and restore contract

Backups are two independent consistency domains: `ledger.db` and `registry.db`.
They are never represented as one atomic cross-service snapshot or watermark.
`create-backup.py` uses SQLite's online backup API, encrypts each completed copy
with `age`, hashes the completed ciphertext, and creates a signed manifest with
`minisign`. It fails closed if encryption, signing, or a required environment
value is unavailable. Plaintext staging is removed on normal completion.

The operator independently publishes the printed checkpoint hash to the approved
external signed journal. This package intentionally does not contain a journal
credential or an automatic egress path. Record that external reference in the
manifest copy held by the release operator.

Run `restore-drill.py` only against a newly created empty drill directory. It
verifies manifest signatures and ciphertext hashes before decryption, runs
`PRAGMA integrity_check`, and never replaces a live database. Retention deletion
is a separately reviewed operator action; `prune.py` supports a dry run by
default and refuses paths outside the configured backup root.
