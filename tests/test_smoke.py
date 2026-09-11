def test_django_setup_imports():
    from django.conf import settings

    assert "src" in settings.INSTALLED_APPS
    assert "default" in settings.DATABASES
    assert "django.contrib.gis" in settings.INSTALLED_APPS
