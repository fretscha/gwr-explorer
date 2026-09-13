import pytest
from django.contrib.gis.geos import Point

from gwr.models import Building

pytestmark = pytest.mark.django_db


def test_building_geom_roundtrip():
    b = Building.objects.create(EGID=1, GDEKT="ZH", geom=Point(2676490, 1235841, srid=2056))
    b.refresh_from_db()
    assert b.geom.srid == 2056
    # transform to WGS84 matches the known reference
    b.geom.transform(4326)
    assert abs(b.geom.x - 8.449423) < 1e-4  # lon
    assert abs(b.geom.y - 47.269041) < 1e-4  # lat
