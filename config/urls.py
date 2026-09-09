from django.urls import include, path

urlpatterns = [path("", include("src.api.urls"))]
