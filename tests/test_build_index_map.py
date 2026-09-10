import math

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_map_points_reprojected():
    from src.models import MapPoint

    call_command("build_index", "--only", "map")
    assert MapPoint.objects.count() == 500
    p = MapPoint.objects.get(egid=1)
    assert math.isclose(p.lat, 47.269041, abs_tol=1e-3)
    assert math.isclose(p.lon, 8.449423, abs_tol=1e-3)
