ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/opt/venv/bin:$PATH

RUN apt-get update \
    && apt-get install --yes --no-install-recommends openssh-client rclone \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv \
    && addgroup --system --gid 10001 registrar \
    && adduser --system --uid 10001 --ingroup registrar --home /nonexistent registrar

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --requirement /app/requirements.txt
COPY --chown=10001:10001 app /app/registrar/app
COPY --chown=10001:10001 migrations /app/registrar/migrations
COPY --chown=10001:10001 verifier /app/registrar/verifier

USER 10001:10001
EXPOSE 8790
CMD ["uvicorn", "registrar.app.main:app", "--host", "0.0.0.0", "--port", "8790", "--workers", "1", "--no-access-log"]
