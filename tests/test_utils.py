from src.utils.field_labels import FIELD_LABELS, field_label


def test_field_label_known():
    assert field_label("GKAT") == "Gebäudekategorie"
    assert field_label("WAZIM") == "Anzahl Zimmer"


def test_field_label_unknown_returns_input():
    assert field_label("XYZ") == "XYZ"


def test_field_labels_cover_core_columns():
    for col in ("EGID", "GBAUJ", "GKODE", "GENH1", "WAREA", "DEINR", "DPLZNAME"):
        assert col in FIELD_LABELS
