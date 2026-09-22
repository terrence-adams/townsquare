-- WS3 item 5: one nullable posts.drive_created_at column, forward-only and
-- additive. Populated from Drive's own createdTime at import promotion time
-- (the only moment that value is in hand for a legacy_import row; posts are
-- immutable after import, so this is the only chance to capture it).
-- No backfill of any other column, and no backfill of existing rows in this
-- column either -- a plain ADD COLUMN with no DEFAULT leaves every existing
-- row NULL, which is correct: nothing before this migration ever observed
-- Drive's createdTime.
ALTER TABLE posts ADD COLUMN drive_created_at TEXT;
