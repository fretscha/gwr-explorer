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

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": GWR_APP_DB},
    "gwr": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"file:{GWR_SOURCE_DB}?mode=ro",
        "OPTIONS": {"uri": True, "init_command": "PRAGMA query_only=1;"},
    },
}
DATABASE_ROUTERS = ["config.db_router.GwrRouter"]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "de-ch"
USE_TZ = True
