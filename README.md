# GWR Explorer

A Django app for searching, browsing and visualizing the Swiss Federal
Register of Buildings and Dwellings (GWR / Gebäude- und Wohnungsregister):
address search, a building detail view, a facet explorer, statistics
dashboards and a map.

## Architecture

The app is backed by a single Postgres/PostGIS database (`default`). GWR
data is loaded straight from the official CSV export (`ch.zip`) via the
`import_gwr` management command, which parses the four bilingual GWR CSVs,
type-converts and geocodes each row (reprojecting Swiss LV95 coordinates to
a PostGIS `geom` column via `ST_Transform`) and loads `Building`, `Entrance`,
`Dwelling` and `Code` tables directly — there is no separate read-only
source database or derived sidecar database as in earlier iterations of this
app. Search uses Postgres full-text search + trigram similarity, the map
queries `geom` with a bbox filter, and the statistics dashboards read a
materialized view (`mv_stats`) refreshed as part of `import_gwr`.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (Python 3.12+ is pinned via
  `.python-version` / `pyproject.toml`)
- Docker, to run the PostGIS database (see Setup below).
- GDAL/GEOS/PROJ available on the host for local (non-Docker) development,
  since GeoDjango loads them via `ctypes` at import time:

  ```bash
  brew install gdal geos proj
  ```

  (Not needed if you only ever run the app inside the Docker container,
  which installs these as system packages — see `docker/Dockerfile`.)

## Setup

Start the PostGIS database (either the compose service or an equivalent
container you already run on port 5433):

```bash
docker compose -f docker/compose.yaml up -d db
```

Then:

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py import_gwr
```

`import_gwr` downloads the current GWR export (~946 MB) from
`https://public.madd.bfs.admin.ch/ch.zip` and loads it — this takes a few
minutes. The download is cached at `data/ch.zip` (overridable via the
`GWR_ZIP_PATH` env var), so **subsequent runs reuse the existing zip instead of
re-downloading**. Pass `--force-download` to refresh that cached zip from the
source before importing, or `--file` to load a zip you already have:

```bash
uv run python manage.py import_gwr                          # reuse cached data/ch.zip
uv run python manage.py import_gwr --force-download         # refresh the cache, then import
uv run python manage.py import_gwr --file /path/to/ch.zip   # use a specific local zip
```

**There is no scheduler or background job.** The register is a point-in-time
snapshot; to refresh it, just re-run `import_gwr` (it is idempotent — safe to
run again against the same or an updated `ch.zip`).

Database connection settings (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`,
`PGDATABASE`) default to the values in `docker/compose.yaml` (host port
`5433`, db/user/password `gwr`) and can be overridden via environment
variables.

## Run

```bash
uv run python manage.py runserver
```

Then open <http://localhost:8000/> — Suche (search), `/statistik/`
(dashboards), `/karte/` (map), `/explorer/` (facet explorer).

## Languages (DE/FR/IT)

The app is trilingual (German, French, Italian; German is the default).
Every page lives under a locale prefix — `/de/`, `/fr/`, `/it/` — added by
Django's `i18n_patterns()` (`config/urls.py`); a bare `/` 302-redirects to
the resolved locale. The header includes a DE/FR/IT switcher (`base.html`)
that posts to Django's built-in `set_language` view
(`/i18n/setlang/`) and redirects back to the current page in the new
language. `LocaleMiddleware` (`config/settings.py`) resolves the active
language per-request from the URL prefix (falling back to the session/
cookie/`Accept-Language` only outside `i18n_patterns`), so switching
language is just a URL change — no separate per-language deployment or
duplicated views.

Two independent things are translated:

- **UI chrome** (nav labels, buttons, static template strings) — standard
  Django `gettext`/`{% trans %}` catalogs under `locale/<lang>/LC_MESSAGES/`.
- **GWR field names and coded values** (e.g. `GKAT` → "Gebäudekategorie" /
  "Catégorie de bâtiment" / "Categoria di edificio", and the coded value
  labels such as `GKAT=1020` → "Gebäude mit ausschliesslicher
  Wohnnutzung") — these come from the official GWR spec PDFs, not from
  hand-translated msgids, since the register defines its own DE/FR/IT
  vocabulary per field and per code. `gwr/services/labels.py`
  (`LabelService`) and `gwr/utils/field_labels.py` resolve both against
  the currently active language (`django.utils.translation.get_language()`),
  so any view or template that calls `LabelService().field(...)` /
  `.value(...)` or `field_label(...)` automatically renders in whichever
  locale the request is in — including the `mv_stats` statistics dashboards,
  which store the raw coded `dim_key` and resolve its display label
  per-language at read time (`gwr/services/stats.py`), rather than baking a
  language into the materialized view.

### Regenerating field labels

`gwr/utils/field_labels.py` (`FIELD_LABELS`, used by `field_label()`) is
**generated**, not hand-written — it's parsed out of the official GWR field
specification PDFs, which are not committed to this repo (see `ch/` in
`.gitignore`). To regenerate it:

```bash
# Requires ch/gebaeude-batiment-edificio_specifications.pdf,
# ch/eingang-entree-entrata_specifications.pdf and
# ch/wohnung-logement-abitazione_specifications.pdf (download from
# https://www.housing-stat.ch/ alongside ch.zip and place them in ch/).
uv run python scripts/gen_field_labels.py
```

### UI chrome translation workflow

Chrome strings (`{% trans %}`/`{% blocktrans %}` in templates, `gettext()`
in Python) go through the normal Django message catalogs in `locale/`.
Run these **from the project root**, not from inside `.venv`, so the scan
is scoped to this project's source (templates/, `gwr/`) and catalogs
(`locale/`) rather than also walking every installed package's own
`locale/` directory under `.venv`:

```bash
uv run python manage.py makemessages -l de -l fr -l it
# edit locale/{de,fr,it}/LC_MESSAGES/django.po, then:
uv run python manage.py compilemessages
```

Both commands may still descend into other installed Django apps' own
`locale/` directories (e.g. `django.contrib.admin`) if they ship
translatable strings — that's expected and harmless. What matters is that
`git status` afterwards only shows changes under this project's own
`locale/*.po`/`locale/*.mo`; never commit changes under `.venv/`.

## Test

```bash
uv run pytest
uv run ruff check .
```

Tests need the PostGIS container running (`docker compose -f
docker/compose.yaml up -d db`) — pytest-django creates and migrates a
`test_gwr` database against it. Tests exercise the real `import_gwr`
pipeline against a small sampled fixture (`tests/fixtures/ch_sample.zip`,
built by `tests/make_csv_fixture.py`), never against production data.

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

`docker/compose.yaml` runs both services: `db` (postgis/postgis, published on
host port 5433) and `app` (built from `docker/Dockerfile`, which installs
GDAL/GEOS/PROJ as system packages so GeoDjango works without host setup).

```bash
docker compose -f docker/compose.yaml up --build
```

`docker/entrypoint.sh` waits for `db` to accept connections, runs `migrate`,
then starts `runserver` on <http://localhost:8000/>. `import_gwr` is not run
automatically (it downloads/loads real data and can take minutes); run it
once after first start, and again whenever you want to refresh the data:

```bash
docker compose -f docker/compose.yaml exec app uv run python manage.py import_gwr
```

The image runs with `DJANGO_DEBUG=1` by default (a dev container, so
`runserver` also serves static assets without a separate collectstatic
step); set `DJANGO_DEBUG=0` in `docker/compose.yaml` to check the
production-style 404/500 error pages locally.
