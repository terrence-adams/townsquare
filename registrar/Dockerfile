# Required: pass an immutable digest, e.g. python@sha256:<verified digest>.
# There is deliberately no mutable-tag default.
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/opt/venv/bin:$PATH

RUN python -m venv /opt/venv \
    && addgroup --system --gid 10001 registrar \
    && adduser --system --uid 10001 --ingroup registrar --home /nonexistent registrar

WORKDIR /app
# Build context is repository root so the reviewed, untracked release wheelhouse
# is available. `resolved.txt` carries transitive hashes; requirements.txt is not
# a release build input.
COPY wheelhouse /wheelhouse
COPY requirements/resolved.txt /wheelhouse/resolved.txt
COPY backup/tool-artifacts.lock.json /opt/townsquare/tool-artifacts.lock.json
COPY backup/verify-tool-artifacts.py /opt/townsquare/verify-tool-artifacts.py
RUN pip install --no-index --find-links=/wheelhouse --require-hashes -r /wheelhouse/resolved.txt
RUN python /opt/townsquare/verify-tool-artifacts.py /wheelhouse/tooling /opt/townsquare/tool-artifacts.lock.json \
 && install -m 0755 /wheelhouse/tooling/minisign /usr/local/bin/minisign
COPY --chown=10001:10001 registrar/app /app/registrar/app
COPY --chown=10001:10001 registrar/migrations /app/registrar/migrations
COPY --chown=10001:10001 registrar/verifier /app/registrar/verifier
COPY --chown=10001:10001 registrar/backup /opt/townsquare/backup

USER 10001:10001
EXPOSE 8790
CMD ["uvicorn", "registrar.app.main:app", "--host", "0.0.0.0", "--port", "8790", "--workers", "1", "--no-access-log"]
