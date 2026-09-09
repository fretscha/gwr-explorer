def test_django_setup_imports():
    from django.conf import settings

    assert "src" in settings.INSTALLED_APPS
    assert "gwr" in settings.DATABASES
