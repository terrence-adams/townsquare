ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE} AS viewer-builder
ENV PIP_NO_CACHE_DIR=1
RUN python -m venv /opt/venv
COPY wheelhouse /wheelhouse
COPY requirements/resolved.txt /wheelhouse/resolved.txt
RUN /opt/venv/bin/pip install --no-index --find-links=/wheelhouse --require-hashes -r /wheelhouse/resolved.txt

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
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH HOME=/tmp \
    STREAMLIT_SERVER_PORT=8502 STREAMLIT_SERVER_ADDRESS=0.0.0.0 STREAMLIT_SERVER_HEADLESS=true STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    TOWNSQUARE_EMBEDDED_RUNTIME_CLASS=${TOWNSQUARE_RUNTIME_CLASS} \
    TOWNSQUARE_EMBEDDED_AUTHORITY_CLASS=${TOWNSQUARE_AUTHORITY_CLASS} \
    TOWNSQUARE_EMBEDDED_CANARY_LABEL=${TOWNSQUARE_CANARY_LABEL} \
    TOWNSQUARE_EMBEDDED_COMPOSE_PROJECT=${TOWNSQUARE_COMPOSE_PROJECT} \
    TOWNSQUARE_EMBEDDED_SOURCE_COMMIT=${TOWNSQUARE_SOURCE_COMMIT} \
    TOWNSQUARE_EMBEDDED_SOURCE_TREE=${TOWNSQUARE_SOURCE_TREE} \
    TOWNSQUARE_EMBEDDED_R7_RELEASE_ID=${TOWNSQUARE_R7_RELEASE_ID} \
    TOWNSQUARE_EMBEDDED_R7_INPUT_MANIFEST_SHA256=${TOWNSQUARE_R7_INPUT_MANIFEST_SHA256} \
    TOWNSQUARE_R7_IDENTITY_SHA256=${TOWNSQUARE_R7_IDENTITY_SHA256}
RUN addgroup --system --gid 10002 viewer && adduser --system --uid 10002 --ingroup viewer --home /nonexistent viewer
COPY --from=viewer-builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=root:root r7-identity.json /opt/townsquare/release/r7-identity.json
COPY --chown=root:root viewer/.streamlit /app/.streamlit
COPY --chown=root:root viewer/app_pages /app/app_pages
COPY --chown=root:root viewer/registrar_client.py viewer/read_gateway.py viewer/views.py viewer/streamlit_app.py /app/
COPY --chown=root:root shared /app/shared
COPY --chown=root:root canary/__init__.py canary/preexec.py /app/canary/
RUN chmod 0444 /opt/townsquare/release/r7-identity.json && find /app /opt/townsquare -type f -exec chmod a-w {} +
USER 10002:10002
EXPOSE 8502 8503
CMD ["python","-m","canary.preexec","--","streamlit","run","streamlit_app.py"]
