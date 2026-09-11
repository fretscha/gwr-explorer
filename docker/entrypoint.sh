#!/bin/sh
set -e

# Wait for Postgres/PostGIS to accept connections before migrating — the app
# container can start well before the db container finishes initializing.
until uv run python -c "
import os, sys
import psycopg
try:
    psycopg.connect(
        host=os.environ.get('PGHOST', '127.0.0.1'),
        port=os.environ.get('PGPORT', '5433'),
        dbname=os.environ.get('PGDATABASE', 'gwr'),
        user=os.environ.get('PGUSER', 'gwr'),
        password=os.environ.get('PGPASSWORD', 'gwr'),
    ).close()
except Exception as exc:
    print(f'waiting for db: {exc}', file=sys.stderr)
    sys.exit(1)
"; do
    sleep 1
done

uv run python manage.py migrate --noinput

exec uv run python manage.py runserver 0.0.0.0:8000
