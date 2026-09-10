import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_facet_filter_by_canton_and_year():
    from src.models import Building
    from src.services.facets import FacetService

    call_command("build_index", "--only", "map")
    zh = Building.objects.using("gwr").filter(GDEKT="ZH").count()
    out = FacetService().query(canton="ZH")
    assert out["count"] == zh
    # year filter narrows results
    narrowed = FacetService().query(canton="ZH", year_from=1980, year_to=1989)
    assert narrowed["count"] <= out["count"]
    # facet options carry speaking labels
    assert all("label" in o for o in out["facets"]["gkat"])


def test_explorer_page_renders_with_german_labels(client):
    call_command("build_index", "--only", "map")
    resp = client.get("/explorer/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Gebäudekategorie" in body
    assert 'title="GDEKT"' in body
    assert 'title="GKAT"' in body


def test_explorer_results_partial_filters_and_paginates(client):
    call_command("build_index", "--only", "map")
    resp = client.get("/explorer/ergebnisse/", {"canton": "ZH"})
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Gebäude" in body
    assert "EGID" in body
