#!/bin/sh
set -e

mkdir -p "$(dirname "$GWR_APP_DB")"

uv run python manage.py migrate --noinput

# The sidecar (search index / map points / stats cache) is a derived,
# point-in-time snapshot of the read-only GWR source. It is intentionally
# NOT rebuilt automatically on every container start (it can take minutes
# over the full dataset) — build/refresh it explicitly, once after first
# start and again whenever data_ch.sqlite changes:
#   docker compose -f docker/compose.yaml exec app uv run python manage.py build_index

exec uv run python manage.py runserver 0.0.0.0:8000
