import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.gis",
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

GWR_ZIP_URL = os.environ.get("GWR_ZIP_URL", "https://public.madd.bfs.admin.ch/ch.zip")

# GeoDjango can't auto-locate Homebrew's GDAL/GEOS on macOS (they aren't on the
# default search paths ctypes.util.find_library() checks); point at them
# explicitly, overridable via env for other hosts (e.g. the Docker image).
GDAL_LIBRARY_PATH = os.environ.get("GDAL_LIBRARY_PATH", "/opt/homebrew/lib/libgdal.dylib")
GEOS_LIBRARY_PATH = os.environ.get("GEOS_LIBRARY_PATH", "/opt/homebrew/lib/libgeos_c.dylib")

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
LANGUAGE_CODE = "de-ch"
USE_TZ = True
