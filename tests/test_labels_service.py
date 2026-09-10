import pytest

from src.services.labels import LabelService

pytestmark = pytest.mark.django_db(databases=["gwr"])


def test_value_and_field_resolution():
    svc = LabelService()
    assert svc.field("GKAT") == "Gebäudekategorie"
    assert svc.value("GKAT", 1020) == "Gebäude mit ausschliesslicher Wohnnutzung"
    assert svc.value("GENH1", 7530) == "Heizöl"
    assert svc.value("GKAT", None) == ""
    assert svc.value("GKAT", 999999) == "999999"
