import pytest

pytestmark = pytest.mark.django_db(databases=["default", "gwr"])


def test_detail_shows_speaking_labels(client):
    resp = client.get("/gebaeude/1/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Gebäudekategorie" in body  # speaking field name
    assert "GKAT" not in body.split("title=")[0]  # raw code not in visible text
    assert "Baujahr des Gebäudes" in body


def test_detail_unknown_egid_404(client):
    assert client.get("/gebaeude/99999999/").status_code == 404
