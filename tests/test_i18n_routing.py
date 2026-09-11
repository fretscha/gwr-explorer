import pytest

pytestmark = pytest.mark.django_db(transaction=True)


def test_bare_root_redirects_to_locale(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert resp["Location"].startswith(("/de/", "/fr/", "/it/"))


@pytest.mark.parametrize("lang", ["de", "fr", "it"])
def test_locale_home_resolves(client, lang):
    assert client.get(f"/{lang}/").status_code == 200
