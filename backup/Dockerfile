ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends age minisign && rm -rf /var/lib/apt/lists/* \
 && addgroup --system --gid 10004 backup && adduser --system --uid 10004 --ingroup backup --home /nonexistent backup
WORKDIR /opt/townsquare/backup
COPY --chown=10004:10004 create-backup.py restore-drill.py prune.py /opt/townsquare/backup/
USER 10004:10004
