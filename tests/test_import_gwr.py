import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_import_loads_typed_rows_and_geometry():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.models import Building, Code, Dwelling, Entrance

    assert Building.objects.count() == 500
    assert Entrance.objects.filter(EGID=1).exists()
    assert Dwelling.objects.filter(EGID=1).count() >= 1
    assert Code.objects.filter(CMERKM="GKAT", CECODID=1020).exists()
    b = Building.objects.get(EGID=1)
    assert b.geom is not None
    b.geom.transform(4326)
    assert abs(b.geom.x - 8.449423) < 1e-4 and abs(b.geom.y - 47.269041) < 1e-4
    assert b.GGDENAME == "Affoltern am Albis"


def test_import_is_idempotent():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.models import Building

    assert Building.objects.count() == 500  # not doubled
