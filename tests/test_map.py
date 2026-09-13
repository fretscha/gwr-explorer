import pytest
from django.core.management import call_command
from django.urls import reverse

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


def test_features_carry_heating_method_and_heated_surface():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.services.maps import MapService

    # Each point must expose GENH1 (heating method, for colour) and GEBF
    # (Energiebezugsfläche / heated surface m², for circle size) so the client
    # can render coloured, size-scaled circles without a second round-trip.
    fc = MapService().points_in_bbox(47.26, 8.44, 47.28, 8.46, {})
    assert fc["features"], "expected at least one building near EGID 1"
    for f in fc["features"]:
        assert "genh1" in f["properties"]
        assert "gebf" in f["properties"]


def test_map_view_hides_points_at_or_above_threshold(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    url = reverse("gwr:map_points")

    # The map only draws objects when fewer than the selected threshold are in
    # view. Default is 250: a world-spanning bbox covers all 500 sample buildings,
    # so the view reports truncated and ships no features (the client shows a
    # "zoom in" hint instead).
    world = {"south": -90, "west": -180, "north": 90, "east": 180}
    resp = client.get(url, world)
    assert resp.status_code == 200
    data = resp.json()
    assert data["truncated"] is True
    assert data["features"] == []


def test_map_view_threshold_is_configurable(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    url = reverse("gwr:map_points")
    world = {"south": -90, "west": -180, "north": 90, "east": 180}

    # Raising the threshold above the sample size (500) draws every point.
    resp = client.get(url, {**world, "limit": 1000})
    data = resp.json()
    assert data["truncated"] is False
    assert data["features"], "expected points below the 1000 threshold"

    # An unsupported value falls back to the 250 default (not honoured verbatim),
    # so a huge bbox is still truncated.
    resp = client.get(url, {**world, "limit": 999999})
    assert resp.json()["truncated"] is True


def test_map_points_bad_bbox_params_return_400(client):
    url = reverse("gwr:map_points")

    # Missing bbox params entirely.
    resp = client.get(url)
    assert resp.status_code == 400

    # Non-numeric south should also 400, not raise a raw 500.
    resp = client.get(url, {"south": "not-a-number", "west": 8.3, "north": 47.6, "east": 8.8})
    assert resp.status_code == 400
