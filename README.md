# GWR Explorer

A Django app for searching, browsing and visualizing the Swiss Federal
Register of Buildings and Dwellings (GWR / Gebäude- und Wohnungsregister):
address search, a building detail view, a facet explorer, statistics
dashboards and a map.

## Two-database design

The app talks to two SQLite databases:

- **`gwr`** — the original, read-only GWR source export (`data_ch.sqlite`,
  ~1.7 GB). Django never writes to it; `config/db_router.py` routes the
  unmanaged `src` models (`Building`, `Entrance`, `Dwelling`, `Code`) to this
  alias and raises if a write is attempted, and the connection itself is
  opened with `mode=ro` plus `PRAGMA query_only=1` as a second guard.
- **`default`** (`app.sqlite`) — a small sidecar database owned by Django
  migrations, holding derived/precomputed data: the FTS5 `search_entrance`
  full-text index, `MapPoint` (reprojected WGS84 coordinates for the map) and
  `StatsCache` (precomputed dashboard aggregates with resolved German
  labels).

The sidecar is built from the source via the `build_index` management
command (see below) and must be rebuilt whenever `data_ch.sqlite` is
refreshed — the app never queries `gwr` directly for search/map/stats, only
for the building detail lookups.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (Python 3.12+ is pinned via
  `.python-version` / `pyproject.toml`)
- The GWR source export, `data_ch.sqlite` (~1.7 GB), placed at the project
  root, or pointed to via the `GWR_SOURCE_DB` environment variable.

## Setup

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py build_index
```

`build_index` reads the (read-only) `gwr` source database and (re)builds the
`default` sidecar database's search index, map points and stats cache. It
takes a minute or two over the full dataset. Useful flags:

- `--only search|map|stats` — rebuild just one artifact.
- `--limit N` — cap the number of source rows read (handy for a quick local
  smoke run instead of the full ~2M+ rows).

**Re-run `build_index` any time `data_ch.sqlite` is replaced/refreshed** —
the sidecar is a point-in-time derived snapshot and does not update itself.

## Run

```bash
uv run python manage.py runserver
```

Then open <http://localhost:8000/> — Suche (search), `/statistik/`
(dashboards), `/karte/` (map), `/explorer/` (facet explorer).

## Test

```bash
uv run pytest
uv run ruff check .
```

Tests run against a small sampled fixture DB (`tests/fixtures/gwr_fixture.sqlite`,
built by `tests/make_fixture.py`) instead of the real `data_ch.sqlite`, and
against an in-memory `default` database — never against production data.

## Styling: Tailwind + Alpine

CSS is built ahead of time with the Tailwind **standalone CLI** (no Node
toolchain required). The binary itself is not committed (see `.gitignore`);
download it once per machine:

```bash
# darwin/arm64:
curl -sL -o tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss
```

(For other platforms, swap `tailwindcss-macos-arm64` for the matching asset
name in the same
[releases page](https://github.com/tailwindlabs/tailwindcss/releases/latest),
e.g. `tailwindcss-linux-x64`. If downloading a standalone binary isn't
possible, `npx tailwindcss` works the same way once Node is available.)

Rebuild `static/css/app.css` after editing templates or
`static/css/tailwind.src.css`:

```bash
./tailwindcss -i static/css/tailwind.src.css -o static/css/app.css --minify
```

Note: the downloaded CLI is Tailwind v4, whose `@source` template-scanning
only takes effect behind the `@import "tailwindcss";` entry point (used in
`tailwind.src.css`) — the legacy `@tailwind base/components/utilities`
directives are parsed for compatibility but don't trigger content scanning
with this CLI version.

`static/vendor/alpine.min.js` is vendored (not fetched from a CDN at
runtime); Alpine isn't heavily used yet but is wired into `base.html` for any
future light interactivity. To refresh it:

```bash
curl -sL -o static/vendor/alpine.min.js https://unpkg.com/alpinejs/dist/cdn.min.js
```

## Docker

A minimal dev container is provided under `docker/`:

```bash
# from the project root, with data_ch.sqlite present
docker compose -f docker/compose.yaml up --build
```

This builds the image, runs `migrate` then `runserver` on container start,
mounts `data_ch.sqlite` read-only, persists `app.sqlite` in a named volume,
and publishes the app on <http://localhost:8000/>. `build_index` is not run
automatically (it can take minutes over the full dataset); run it once after
first start and again whenever `data_ch.sqlite` changes:

```bash
docker compose -f docker/compose.yaml exec app uv run python manage.py build_index
```

The image runs with `DJANGO_DEBUG=1` by default (a dev container, so
`runserver` also serves static assets without a separate collectstatic
step); set `DJANGO_DEBUG=0` in `docker/compose.yaml` to check the
production-style 404/500 error pages locally.
