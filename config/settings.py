import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "src",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

GWR_SOURCE_DB = os.environ.get("GWR_SOURCE_DB", str(BASE_DIR / "data_ch.sqlite"))
GWR_APP_DB = os.environ.get("GWR_APP_DB", str(BASE_DIR / "app.sqlite"))

# Sqlite OPTIONS for opening the "gwr" alias read-only. Shared with
# tests/conftest.py (which points this same alias at a sampled fixture file
# instead of GWR_SOURCE_DB) so the two never drift apart.
GWR_READONLY_OPTIONS = {"uri": True, "init_command": "PRAGMA query_only=1;"}

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": GWR_APP_DB},
    "gwr": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"file:{GWR_SOURCE_DB}?mode=ro",
        "OPTIONS": GWR_READONLY_OPTIONS,
        # gwr is a standalone read-only source DB with no FK relationship to "default"
        # (allow_migrate already forbids migrating it). This normally guards against
        # Django's test runner assuming every non-default alias depends on "default"
        # ("Circular dependency in TEST[DEPENDENCIES]") when a test requests only
        # databases=["gwr"]. In this project tests/conftest.py's custom
        # django_db_setup fixture calls setup_databases() with an explicit aliases
        # list that excludes "gwr" entirely, so that check never runs today — this
        # is kept as belt-and-suspenders in case anything ever falls back to
        # pytest-django's stock alias-from-markers behavior for this DB.
        "TEST": {"DEPENDENCIES": []},
    },
}
DATABASE_ROUTERS = ["config.db_router.GwrRouter"]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "de-ch"
USE_TZ = True
