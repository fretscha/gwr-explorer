from django.urls import path

from src.api import api_views, views

app_name = "gwr"
urlpatterns = [
    path("", views.search, name="search"),
    path("suche/", views.search_results, name="search_results"),
    path("gebaeude/<int:egid>/", views.building_detail, name="building_detail"),
    path("explorer/", views.explorer, name="explorer"),
    path("explorer/ergebnisse/", views.explorer_results, name="explorer_results"),
    path("statistik/", views.stats, name="stats"),
    path("api/stats/<str:metric>/", api_views.stats_json, name="stats_json"),
]
