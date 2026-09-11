FROM python:3.12-slim

# GeoDjango needs the GDAL/GEOS/PROJ shared libs (and binutils, which
# ctypes.util.find_library() shells out to via `objdump` on some platforms)
# available at runtime, not just at build time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils libproj-dev gdal-bin libgdal-dev libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# uv gives us fast, reproducible installs from uv.lock without needing a
# separate pip/venv dance in the image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifests first so dependency install is cached separately
# from application code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT ["docker/entrypoint.sh"]
