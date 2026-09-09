import pytest
from django.conf import settings
from django.db import connections
from django.test.utils import setup_databases, teardown_databases
from pytest_django.fixtures import _disable_migrations

from tests.make_fixture import FIXTURE_PATH

# Read-only sqlite URI pointing at the small sampled fixture (never the real
# 1.7GB data_ch.sqlite source configured in settings for production use).
_GWR_FIXTURE_URI = f"file:{FIXTURE_PATH}?mode=ro"


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker, django_db_use_migrations):
    """Override pytest-django's default test-DB bring-up.

    Every writable alias (currently just `default`; a future managed alias
    would be picked up automatically) still gets a normal, ephemeral
    pytest-django test database. Later tasks add MANAGED models —
    MapPoint/StatsCache — there, which need migrations (or, per
    `addopts = "--no-migrations"` in pyproject.toml, a `run_syncdb`-style
    table creation straight from the models) run against it.

    `gwr` must NEVER go through Django's create/clone/destroy test-database
    dance: its production NAME points at the real 1.7GB `data_ch.sqlite`
    source, and letting the test runner attempt to create/copy/migrate a test
    database from that would be catastrophic (slow at best, destructive at
    worst). Instead we repoint the `gwr` alias straight at the small,
    read-only sampled fixture *before* setup_databases runs, and pass an
    explicit aliases list (everything except "gwr") so setup_databases never
    even considers "gwr" for test-db creation.
    """
    # Because this fixture fully replaces pytest-django's stock
    # `django_db_setup`, we must manually honor `--no-migrations`
    # (django_db_use_migrations=False): mirror what the stock fixture does
    # and disable migrations *before* setup_databases() creates the
    # "default" test DB, so its tables come from run_syncdb against the
    # current models rather than migration files. Without this,
    # `addopts = "--no-migrations"` would silently do nothing.
    if not django_db_use_migrations:
        _disable_migrations()

    # NOTE: only NAME/OPTIONS are touched here — the "TEST" sub-dict is left
    # alone. By this point Django's ConnectionHandler.configure_settings() has
    # already normalized it (filling in CHARSET/COLLATION/MIGRATE/MIRROR/NAME
    # defaults alongside the DEPENDENCIES: [] from settings.py); replacing the
    # whole dict here would drop those defaults and break pytest-django's
    # _databases_names() (KeyError: 'MIRROR').
    gwr_settings = settings.DATABASES["gwr"]
    gwr_settings["NAME"] = _GWR_FIXTURE_URI
    gwr_settings["OPTIONS"] = settings.GWR_READONLY_OPTIONS

    # Every alias except "gwr" gets the normal test-DB treatment. Derived
    # dynamically (rather than hardcoded to ["default"]) so a future writable
    # alias is picked up automatically instead of silently skipped.
    writable_aliases = [alias for alias in settings.DATABASES if alias != "gwr"]

    with django_db_blocker.unblock():
        db_cfg = setup_databases(verbosity=0, interactive=False, aliases=writable_aliases)

    # Force the "gwr" connection (if Django already lazily opened one against
    # the pre-test settings) to reconnect using the fixture path set above.
    connections["gwr"].close()
    connections["gwr"].settings_dict["NAME"] = _GWR_FIXTURE_URI
    connections["gwr"].settings_dict["OPTIONS"] = settings.GWR_READONLY_OPTIONS

    yield

    with django_db_blocker.unblock():
        teardown_databases(db_cfg, verbosity=0)
