FROM python:3.12-slim

# uv gives us fast, reproducible installs from uv.lock without needing a
# separate pip/venv dance in the image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifests first so dependency install is cached separately
# from application code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

# This is a local dev image: DEBUG stays on so `runserver` also serves
# static assets (app.css, vendored JS) without a separate collectstatic /
# WhiteNoise setup. Override DJANGO_DEBUG=0 to check the production error
# pages (404.html/500.html) locally.
ENV PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=1 \
    GWR_SOURCE_DB=/app/data_ch.sqlite \
    GWR_APP_DB=/app/data/app.sqlite

EXPOSE 8000

ENTRYPOINT ["docker/entrypoint.sh"]
