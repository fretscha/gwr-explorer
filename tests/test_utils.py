import math

from src.utils.buckets import area_bucket, decade
from src.utils.coords import CoordTransform
from src.utils.field_labels import FIELD_LABELS, field_label


def test_field_label_known():
    assert field_label("GKAT") == "Gebäudekategorie"
    assert field_label("WAZIM") == "Anzahl Zimmer"


def test_field_label_unknown_returns_input():
    assert field_label("XYZ") == "XYZ"


def test_field_labels_cover_core_columns():
    for col in ("EGID", "GBAUJ", "GKODE", "GENH1", "WAREA", "DEINR", "DPLZNAME"):
        assert col in FIELD_LABELS


def test_coord_transform_lv95_origin():
    lat, lon = CoordTransform().to_wgs84(2600000, 1200000)
    assert math.isclose(lat, 46.951083, abs_tol=1e-4)
    assert math.isclose(lon, 7.438632, abs_tol=1e-4)


def test_coord_transform_affoltern():
    lat, lon = CoordTransform().to_wgs84(2676490, 1235841)
    assert math.isclose(lat, 47.269041, abs_tol=1e-4)
    assert math.isclose(lon, 8.449423, abs_tol=1e-4)


def test_decade():
    assert decade(1984) == "1980er"
    assert decade(None) is None


def test_area_bucket():
    assert area_bucket(45) == "< 50 m²"
    assert area_bucket(150) == "100–199 m²"
    assert area_bucket(None) is None
