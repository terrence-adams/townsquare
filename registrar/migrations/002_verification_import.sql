CREATE TABLE verification_reports(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_uid TEXT NOT NULL REFERENCES posts(post_uid) ON DELETE RESTRICT,
  verifier_principal TEXT NOT NULL,
  observed_json TEXT NOT NULL,
  valid INTEGER NOT NULL CHECK(valid IN (0,1)),
  evidence TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE import_runs(
  run_id TEXT PRIMARY KEY,
  manifest_digest TEXT NOT NULL,
  manifest_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('validated','promoted')),
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  promoted_at TEXT
);
CREATE INDEX idx_verification_post ON verification_reports(post_uid,created_at);
