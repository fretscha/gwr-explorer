import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_detail_speaking_labels(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    resp = client.get("/gebaeude/1/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Gebäudekategorie" in body and "Baujahr des Gebäudes" in body
    assert "GKAT" not in body.split("title=")[0]


def test_detail_404(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    assert client.get("/gebaeude/99999999/").status_code == 404
