FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.5
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --output-file /tmp/requirements.txt \
    && python -m venv .venv \
    && .venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY deploy/entrypoint.sh /app/entrypoint.sh
RUN groupadd --gid 10001 shieldmate \
    && useradd --uid 10001 --gid shieldmate --no-create-home shieldmate \
    && mkdir /app/storage /app/backups \
    && chown shieldmate:shieldmate /app/storage /app/backups \
    && chmod 700 /app/storage /app/backups \
    && chmod 555 /app/entrypoint.sh
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh", "-c", ".venv/bin/alembic upgrade head && exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log --no-server-header"]
