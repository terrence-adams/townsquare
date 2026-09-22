ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

# HOME=/tmp because the rootfs is read-only in Compose and Streamlit still
# wants a writable ~/.streamlit; /tmp is the tmpfs the service mounts.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/opt/venv/bin:$PATH \
    HOME=/tmp \
    STREAMLIT_SERVER_PORT=8502 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# No openssh-client, no rclone: unlike the Registrar image this one has no
# reason to reach anything but the Registrar's HTTP port. UID 10002 so it is
# never confused with the Registrar's own 10001.
RUN python -m venv /opt/venv \
    && addgroup --system --gid 10002 viewer \
    && adduser --system --uid 10002 --ingroup viewer --home /nonexistent viewer

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --requirement /app/requirements.txt
COPY --chown=10002:10002 .streamlit /app/.streamlit
COPY --chown=10002:10002 app_pages /app/app_pages
COPY --chown=10002:10002 registrar_client.py views.py streamlit_app.py /app/

USER 10002:10002
EXPOSE 8502
CMD ["streamlit", "run", "streamlit_app.py"]
