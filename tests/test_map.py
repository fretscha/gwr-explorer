import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_bbox_returns_in_view_and_caps():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.services.maps import MapService

    # EGID 1 is near 8.449E/47.269N
    fc = MapService().points_in_bbox(47.26, 8.44, 47.28, 8.46, {})
    egids = [f["properties"]["egid"] for f in fc["features"]]
    assert 1 in egids
    for f in fc["features"]:
        lon, lat = f["geometry"]["coordinates"]
        assert 8.44 <= lon <= 8.46 and 47.26 <= lat <= 47.28
    empty = MapService().points_in_bbox(0, 0, 0.001, 0.001, {})
    assert empty["features"] == []
    capped = MapService().points_in_bbox(-90, -180, 90, 180, {}, cap=10)
    assert capped["truncated"] is True and len(capped["features"]) == 10
