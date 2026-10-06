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
 && addgroup --system --gid 10004 backup && adduser --system --uid 10004 --ingroup backup --home /nonexistent backup
WORKDIR /opt/townsquare/backup
COPY --chown=10004:10004 backup/create-backup.py backup/restore-drill.py backup/prune.py /opt/townsquare/backup/
USER 10004:10004
