ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE} AS ledger-builder
ENV PIP_NO_CACHE_DIR=1
RUN python -m venv /opt/venv
COPY wheelhouse /wheelhouse
COPY requirements/resolved.txt /wheelhouse/resolved.txt
RUN /opt/venv/bin/pip install --no-index --find-links=/wheelhouse --require-hashes -r /wheelhouse/resolved.txt
COPY wheelhouse/tooling/age /verify/tools/age
COPY wheelhouse/tooling/minisign /verify/tools/minisign
COPY backup/tool-artifacts.lock.json backup/verify-tool-artifacts.py /verify/
RUN python /verify/verify-tool-artifacts.py /verify/tools /verify/tool-artifacts.lock.json \
 && install -d -m 0755 /verified && install -m 0755 /verify/tools/minisign /verified/minisign

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
      townsquare.r7-release-id="${TOWNSQUARE_R7_RELEASE_ID}" townsquare.r7-identity-sha256="${TOWNSQUARE_R7_IDENTITY_SHA256}"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH \
    TOWNSQUARE_EMBEDDED_RUNTIME_CLASS=${TOWNSQUARE_RUNTIME_CLASS} \
    TOWNSQUARE_EMBEDDED_AUTHORITY_CLASS=${TOWNSQUARE_AUTHORITY_CLASS} \
    TOWNSQUARE_EMBEDDED_CANARY_LABEL=${TOWNSQUARE_CANARY_LABEL} \
    TOWNSQUARE_EMBEDDED_COMPOSE_PROJECT=${TOWNSQUARE_COMPOSE_PROJECT} \
    TOWNSQUARE_EMBEDDED_SOURCE_COMMIT=${TOWNSQUARE_SOURCE_COMMIT} \
    TOWNSQUARE_EMBEDDED_SOURCE_TREE=${TOWNSQUARE_SOURCE_TREE} \
    TOWNSQUARE_EMBEDDED_R7_RELEASE_ID=${TOWNSQUARE_R7_RELEASE_ID} \
    TOWNSQUARE_EMBEDDED_R7_INPUT_MANIFEST_SHA256=${TOWNSQUARE_R7_INPUT_MANIFEST_SHA256} \
    TOWNSQUARE_R7_IDENTITY_SHA256=${TOWNSQUARE_R7_IDENTITY_SHA256}
RUN addgroup --system --gid 10001 registrar && adduser --system --uid 10001 --ingroup registrar --home /nonexistent registrar
COPY --from=ledger-builder /opt/venv /opt/venv
COPY --from=ledger-builder --chown=root:root /verified/minisign /usr/local/bin/minisign
WORKDIR /app
COPY --chown=root:root r7-identity.json /opt/townsquare/release/r7-identity.json
COPY --chown=root:root registrar/app /app/registrar/app
COPY --chown=root:root shared /app/shared
COPY --chown=root:root canary/__init__.py canary/preexec.py canary/bootstrap.py canary/safe_archive.py /app/canary/
COPY --chown=root:root registrar/migrations /app/registrar/migrations
COPY --chown=root:root registrar/verifier /app/registrar/verifier
COPY --chown=root:root contracts/r7/ledger-migrations.json /app/contracts/r7/ledger-migrations.json
RUN chmod 0444 /opt/townsquare/release/r7-identity.json && find /app /opt/townsquare -type f -exec chmod a-w {} +
USER 10001:10001
EXPOSE 8790
CMD ["python","-m","canary.preexec","--","uvicorn","registrar.app.main:app","--host","0.0.0.0","--port","8790","--workers","1","--no-access-log"]
