from django.urls import path

from src.api import views

app_name = "gwr"
urlpatterns = [
    path("", views.search, name="search"),
    path("suche/", views.search_results, name="search_results"),
]
