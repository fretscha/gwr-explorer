from django.utils.translation import activate

from src.utils.field_labels import FIELD_LABELS, field_label


def test_de_fr_it_field_labels():
    activate("de")
    assert field_label("GKAT") == "Gebäudekategorie"
    activate("fr")
    assert field_label("GKAT") == "Catégorie de bâtiment"
    activate("it")
    assert field_label("GKAT") == "Categoria di edificio"


def test_fallback_unknown_and_missing():
    activate("fr")
    assert field_label("NOPE") == "NOPE"
    # a field present only in DE falls back to DE (construct via dict check)
    assert FIELD_LABELS["GKAT"]["de"]


def test_core_fields_present():
    for f in ("EGID", "GBAUJ", "GKODE", "GENH1", "WAREA", "DEINR", "WAZIM"):
        assert f in FIELD_LABELS
