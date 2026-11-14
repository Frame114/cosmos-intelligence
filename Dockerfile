FROM python:3.12.16-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY alembic ./alembic

RUN pip install --no-cache-dir . \
    && groupadd --system --gid 10001 cosmos \
    && useradd --system --uid 10001 --gid cosmos --home-dir /nonexistent cosmos

USER 10001:10001

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
