# Immutable digest required by the release build command; no mutable base default.
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE} AS registry-tool-verifier
COPY wheelhouse/tooling/age /verify/tools/age
COPY wheelhouse/tooling/minisign /verify/tools/minisign
COPY backup/tool-artifacts.lock.json backup/verify-tool-artifacts.py /verify/
RUN python /verify/verify-tool-artifacts.py /verify/tools /verify/tool-artifacts.lock.json \
 && test -f /verify/tools/minisign \
 && test ! -L /verify/tools/minisign \
 && install -d -o root -g root -m 0755 /verified \
 && install -o root -g root -m 0755 /verify/tools/minisign /verified/minisign

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
LABEL org.opencontainers.image.revision="${TOWNSQUARE_SOURCE_COMMIT}" \
      org.opencontainers.image.source-tree="${TOWNSQUARE_SOURCE_TREE}" \
      townsquare.runtime-class="${TOWNSQUARE_RUNTIME_CLASS}" \
      townsquare.authority-class="${TOWNSQUARE_AUTHORITY_CLASS}" \
      townsquare.canary-label="${TOWNSQUARE_CANARY_LABEL}" \
      townsquare.compose-project="${TOWNSQUARE_COMPOSE_PROJECT}"
LABEL townsquare.r7-release-id="${TOWNSQUARE_R7_RELEASE_ID}" \
      townsquare.r7-identity-sha256="${TOWNSQUARE_R7_IDENTITY_SHA256}"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOWNSQUARE_EMBEDDED_RUNTIME_CLASS=${TOWNSQUARE_RUNTIME_CLASS} \
    TOWNSQUARE_EMBEDDED_AUTHORITY_CLASS=${TOWNSQUARE_AUTHORITY_CLASS} \
    TOWNSQUARE_EMBEDDED_CANARY_LABEL=${TOWNSQUARE_CANARY_LABEL} \
    TOWNSQUARE_EMBEDDED_COMPOSE_PROJECT=${TOWNSQUARE_COMPOSE_PROJECT} \
    TOWNSQUARE_EMBEDDED_SOURCE_COMMIT=${TOWNSQUARE_SOURCE_COMMIT} \
    TOWNSQUARE_EMBEDDED_SOURCE_TREE=${TOWNSQUARE_SOURCE_TREE} \
    TOWNSQUARE_EMBEDDED_R7_RELEASE_ID=${TOWNSQUARE_R7_RELEASE_ID} \
    TOWNSQUARE_EMBEDDED_R7_INPUT_MANIFEST_SHA256=${TOWNSQUARE_R7_INPUT_MANIFEST_SHA256} \
    TOWNSQUARE_R7_IDENTITY_SHA256=${TOWNSQUARE_R7_IDENTITY_SHA256}
RUN addgroup --system --gid 10003 registry && adduser --system --uid 10003 --ingroup registry --home /nonexistent registry
COPY --from=registry-tool-verifier --chown=root:root /verified/minisign /usr/local/bin/minisign
WORKDIR /app
COPY --chown=root:root r7-identity.json /opt/townsquare/release/r7-identity.json
COPY --chown=10003:10003 registry/app.py registry/migrate.py registry/schema.sql /app/
COPY --chown=root:root contracts/r7/registry-schema.json /contracts/r7/registry-schema.json
COPY --chown=10003:10003 shared /app/shared
COPY --chown=10003:10003 canary/__init__.py canary/preexec.py /app/canary/
RUN chmod 0444 /opt/townsquare/release/r7-identity.json && find /app /opt/townsquare -type f -exec chmod a-w {} +
USER 10003:10003
EXPOSE 8789
CMD ["python","-m","canary.preexec","--","python","/app/app.py"]
