import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


@pytest.mark.parametrize("url", ["/", "/statistik/", "/karte/", "/explorer/", "/gebaeude/1/"])
def test_pages_return_200(client, url):
    call_command("build_index")
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"GWR" in resp.content
