import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_facet_filter_and_labels():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.models import Building
    from src.services.facets import FacetService

    zh = Building.objects.filter(GDEKT="ZH").count()
    out = FacetService().query(canton="ZH")
    assert out["count"] == zh
    assert all("label" in o for o in out["facets"]["gkat"])
    narrowed = FacetService().query(canton="ZH", year_from=1980, year_to=1989)
    assert narrowed["count"] <= out["count"]
