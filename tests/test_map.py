import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_bbox_returns_only_points_in_view():
    from src.models import MapPoint
    from src.services.maps import MapService

    call_command("build_index", "--only", "map")
    p = MapPoint.objects.get(egid=1)
    # tiny bbox around EGID 1 includes it
    fc = MapService().points_in_bbox(p.lat - 0.01, p.lon - 0.01, p.lat + 0.01, p.lon + 0.01, {})
    egids = [f["properties"]["egid"] for f in fc["features"]]
    assert 1 in egids
    # far-away bbox excludes it
    empty = MapService().points_in_bbox(0.0, 0.0, 0.001, 0.001, {})
    assert empty["features"] == []


def test_bbox_cap_sets_truncated():
    from src.services.maps import MapService

    call_command("build_index", "--only", "map")
    fc = MapService().points_in_bbox(-90, -180, 90, 180, {}, cap=10)
    assert fc["truncated"] is True
    assert len(fc["features"]) == 10
