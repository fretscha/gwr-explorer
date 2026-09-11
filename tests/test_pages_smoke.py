import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "url",
    [
        "/de/",
        "/de/statistik/",
        "/de/karte/",
        "/de/explorer/",
        "/de/gebaeude/1/",
        "/fr/gebaeude/1/",
    ],
)
def test_pages_200(client, url):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"GWR" in resp.content
