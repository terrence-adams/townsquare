# Test-only checkpoint-signing fixture

No private key is checked into this repository. The test fixture is generated
only in a disposable operator environment with `minisign` already installed:

```text
minisign -G -s tests/evidence/TEST-ONLY-DO-NOT-DEPLOY.key -p tests/evidence/TEST-ONLY-DO-NOT-DEPLOY.pub
python backup/operator-sign-checkpoint.py tests/evidence/checkpoint.request.json --secret-key tests/evidence/TEST-ONLY-DO-NOT-DEPLOY.key --output tests/evidence/checkpoint.request.minisig
python backup/verify-checkpoint.py tests/evidence/checkpoint.request.json tests/evidence/checkpoint.request.minisig --public-key tests/evidence/TEST-ONLY-DO-NOT-DEPLOY.pub
```

Destroy the private key immediately after the test. The current local environment
does not provide `minisign`, so no signing algorithm execution or fabricated key
fixture was produced. Production signing keys remain external and operator-controlled.
