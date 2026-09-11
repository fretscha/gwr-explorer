import pytest
from django.core.management import call_command

from src.services.labels import LabelService
from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_value_and_field_resolution():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    svc = LabelService()
    assert svc.field("GKAT") == "Gebäudekategorie"
    assert svc.value("GKAT", 1020) == "Gebäude mit ausschliesslicher Wohnnutzung"
    assert svc.value("GENH1", 7530) == "Heizöl"
    assert svc.value("GKAT", None) == ""
    assert svc.value("GKAT", 999999) == "999999"
