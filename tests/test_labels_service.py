import pytest
from django.core.management import call_command
from django.utils.translation import activate

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_value_and_field_per_language():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    from src.services.labels import LabelService

    svc = LabelService()
    activate("de")
    assert svc.field("GKAT") == "Gebäudekategorie"
    assert svc.value("GKAT", 1020) == "Gebäude mit ausschliesslicher Wohnnutzung"
    activate("fr")
    assert svc.field("GKAT") == "Catégorie de bâtiment"
    assert svc.value("GKAT", 1020)  # French text present, non-empty, != German
    assert svc.value("GKAT", 1020) != "Gebäude mit ausschliesslicher Wohnnutzung"
    assert svc.value("GKAT", None) == ""
    # Unknown code: no catalog entry, so the raw code is returned as-is.
    assert svc.value("GKAT", 999999) == "999999"
