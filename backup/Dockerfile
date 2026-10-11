ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
ARG TOWNSQUARE_RUNTIME_CLASS
ARG TOWNSQUARE_AUTHORITY_CLASS
ARG TOWNSQUARE_CANARY_LABEL
ARG TOWNSQUARE_COMPOSE_PROJECT
ARG TOWNSQUARE_SOURCE_COMMIT
ARG TOWNSQUARE_SOURCE_TREE
ARG TOWNSQUARE_R7_RELEASE_ID
ARG TOWNSQUARE_R7_INPUT_MANIFEST_SHA256
ARG TOWNSQUARE_R7_IDENTITY_SHA256
LABEL org.opencontainers.image.revision="${TOWNSQUARE_SOURCE_COMMIT}" org.opencontainers.image.source-tree="${TOWNSQUARE_SOURCE_TREE}" \
      townsquare.runtime-class="${TOWNSQUARE_RUNTIME_CLASS}" townsquare.authority-class="${TOWNSQUARE_AUTHORITY_CLASS}" townsquare.canary-label="${TOWNSQUARE_CANARY_LABEL}" townsquare.compose-project="${TOWNSQUARE_COMPOSE_PROJECT}" \
      townsquare.r7-release-id="${TOWNSQUARE_R7_RELEASE_ID}" townsquare.r7-input-manifest-sha256="${TOWNSQUARE_R7_INPUT_MANIFEST_SHA256}" townsquare.r7-identity-sha256="${TOWNSQUARE_R7_IDENTITY_SHA256}"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/opt/townsquare \
    TOWNSQUARE_EMBEDDED_RUNTIME_CLASS=${TOWNSQUARE_RUNTIME_CLASS} \
    TOWNSQUARE_EMBEDDED_AUTHORITY_CLASS=${TOWNSQUARE_AUTHORITY_CLASS} \
    TOWNSQUARE_EMBEDDED_CANARY_LABEL=${TOWNSQUARE_CANARY_LABEL} \
    TOWNSQUARE_EMBEDDED_COMPOSE_PROJECT=${TOWNSQUARE_COMPOSE_PROJECT} \
    TOWNSQUARE_EMBEDDED_SOURCE_COMMIT=${TOWNSQUARE_SOURCE_COMMIT} \
    TOWNSQUARE_EMBEDDED_SOURCE_TREE=${TOWNSQUARE_SOURCE_TREE} \
    TOWNSQUARE_EMBEDDED_R7_RELEASE_ID=${TOWNSQUARE_R7_RELEASE_ID} \
    TOWNSQUARE_EMBEDDED_R7_INPUT_MANIFEST_SHA256=${TOWNSQUARE_R7_INPUT_MANIFEST_SHA256} \
    TOWNSQUARE_R7_IDENTITY_SHA256=${TOWNSQUARE_R7_IDENTITY_SHA256} \
    TOWNSQUARE_EMBEDDED_R7_IDENTITY_SHA256=${TOWNSQUARE_R7_IDENTITY_SHA256}
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
COPY --chown=root:root r7-identity.json /opt/townsquare/release/r7-identity.json
COPY --chown=10004:10004 backup/create-backup.py backup/restore-drill.py backup/recovery_replay_drill.py backup/prune.py /opt/townsquare/backup/
COPY --chown=10004:10004 registrar/app/__init__.py registrar/app/db.py registrar/app/filename.py registrar/app/service.py registrar/app/native_ledger.py /opt/townsquare/registrar/app/
COPY --chown=10004:10004 registry/app.py /opt/townsquare/registry/app.py
COPY --chown=root:root shared /opt/townsquare/shared
COPY --chown=root:root canary/__init__.py canary/preexec.py /opt/townsquare/canary/
RUN chmod 0444 /opt/townsquare/release/r7-identity.json && find /opt/townsquare -type f -exec chmod a-w {} +
USER 10004:10004
ENTRYPOINT ["python","-m","canary.preexec","--"]
CMD ["python","/opt/townsquare/backup/create-backup.py"]
