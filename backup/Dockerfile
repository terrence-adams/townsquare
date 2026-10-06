ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
# Versions are required release build arguments, captured with the base digest.
ARG AGE_VERSION
ARG MINISIGN_VERSION
RUN test -n "$AGE_VERSION" && test -n "$MINISIGN_VERSION" \
 && apt-get update && apt-get install -y --no-install-recommends age=${AGE_VERSION} minisign=${MINISIGN_VERSION} && rm -rf /var/lib/apt/lists/* \
 && addgroup --system --gid 10004 backup && adduser --system --uid 10004 --ingroup backup --home /nonexistent backup
WORKDIR /opt/townsquare/backup
COPY --chown=10004:10004 backup/create-backup.py backup/restore-drill.py backup/prune.py /opt/townsquare/backup/
USER 10004:10004
