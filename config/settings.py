import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.gis",
    "django.contrib.sessions",
    "src",
]

# Order matters: SessionMiddleware must run before LocaleMiddleware (set_language
# and the language cookie/session need the session available), LocaleMiddleware
# before CommonMiddleware (so the resolved language is set before CommonMiddleware
# processes the request), and CsrfViewMiddleware is required by the set_language
# view (it's a POST endpoint protected by Django's CSRF middleware).
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
            ]
        },
    }
]

GWR_ZIP_URL = os.environ.get("GWR_ZIP_URL", "https://public.madd.bfs.admin.ch/ch.zip")

# GeoDjango can't auto-locate Homebrew's GDAL/GEOS on macOS (they aren't on the
# default search paths ctypes.util.find_library() checks); point at them
# explicitly on this host. Prefer an env override; otherwise use the Homebrew
# path only if it actually exists on disk. On Linux (e.g. the Docker image)
# neither the env var nor the Homebrew path is present, so we leave the
# setting undefined entirely -- a truthy-but-wrong path makes GeoDjango skip
# auto-detection and CDLL() it directly, raising OSError. Leaving it unset
# lets GeoDjango auto-detect the apt-installed libs on Linux.
_gdal = os.environ.get("GDAL_LIBRARY_PATH") or (
    "/opt/homebrew/lib/libgdal.dylib" if os.path.exists("/opt/homebrew/lib/libgdal.dylib") else None
)
if _gdal:
    GDAL_LIBRARY_PATH = _gdal
_geos = os.environ.get("GEOS_LIBRARY_PATH") or (
    "/opt/homebrew/lib/libgeos_c.dylib" if os.path.exists("/opt/homebrew/lib/libgeos_c.dylib") else None
)
if _geos:
    GEOS_LIBRARY_PATH = _geos

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("PGDATABASE", "gwr"),
        "USER": os.environ.get("PGUSER", "gwr"),
        "PASSWORD": os.environ.get("PGPASSWORD", "gwr"),
        "HOST": os.environ.get("PGHOST", "127.0.0.1"),
        "PORT": os.environ.get("PGPORT", "5433"),
    },
}

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_I18N = True
LANGUAGE_CODE = "de"
LANGUAGES = [
    ("de", _("German")),
    ("fr", _("French")),
    ("it", _("Italian")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

USE_TZ = True
