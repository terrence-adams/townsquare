CREATE TABLE verifier_nonces(key_id TEXT NOT NULL,nonce TEXT NOT NULL,used_at TEXT NOT NULL,PRIMARY KEY(key_id,nonce));
