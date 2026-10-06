ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
# Staged public Linux artifacts are copied from wheelhouse/tooling; the verifier
# fails closed until their exact filenames, versions, and hashes are reviewed.
COPY wheelhouse /wheelhouse
COPY backup/tool-artifacts.lock.json /opt/townsquare/tool-artifacts.lock.json
COPY backup/verify-tool-artifacts.py /opt/townsquare/verify-tool-artifacts.py
RUN python /opt/townsquare/verify-tool-artifacts.py /wheelhouse/tooling /opt/townsquare/tool-artifacts.lock.json \
 && install -m 0755 /wheelhouse/tooling/age /usr/local/bin/age \
 && install -m 0755 /wheelhouse/tooling/minisign /usr/local/bin/minisign \
 && addgroup --system --gid 10004 townsquare-backup && adduser --system --uid 10004 --ingroup townsquare-backup --home /nonexistent townsquare-backup
WORKDIR /opt/townsquare/backup
COPY --chown=10004:10004 backup/create-backup.py backup/restore-drill.py backup/recovery_replay_drill.py backup/prune.py /opt/townsquare/backup/
COPY --chown=10004:10004 registrar/app/__init__.py registrar/app/db.py registrar/app/filename.py registrar/app/service.py registrar/app/native_ledger.py /opt/townsquare/registrar/app/
COPY --chown=10004:10004 registry/app.py /opt/townsquare/registry/app.py
USER 10004:10004
