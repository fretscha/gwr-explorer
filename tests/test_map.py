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


def test_map_points_bad_bbox_params_return_400(client):
    # Missing bbox params entirely.
    resp = client.get("/api/map/points/")
    assert resp.status_code == 400

    # Non-numeric south should also 400, not raise a raw 500.
    resp = client.get("/api/map/points/", {"south": "not-a-number", "west": 8.3, "north": 47.6, "east": 8.8})
    assert resp.status_code == 400
