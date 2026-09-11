from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.views.i18n import set_language

urlpatterns = [
    # Outside i18n_patterns: the language-switch endpoint itself must be
    # reachable without a locale prefix already resolved.
    path("i18n/setlang/", set_language, name="set_language"),
    *i18n_patterns(path("", include("src.api.urls")), prefix_default_language=True),
]
