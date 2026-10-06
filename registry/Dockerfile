# Immutable digest required by the release build command; no mutable base default.
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN addgroup --system --gid 10003 registry && adduser --system --uid 10003 --ingroup registry --home /nonexistent registry
WORKDIR /app
COPY --chown=10003:10003 registry/app.py registry/migrate.py registry/schema.sql /app/
USER 10003:10003
EXPOSE 8789
CMD ["python","/app/app.py"]
