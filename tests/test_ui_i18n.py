import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_french_chrome_and_labels(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    body = client.get("/fr/gebaeude/1/").content.decode()
    assert "Catégorie de bâtiment" in body  # FR field name
    assert "Gebäudekategorie" not in body  # not German
    assert "Recherche" in body  # translated chrome (nav label)

    it = client.get("/it/gebaeude/1/").content.decode()
    assert "Categoria di edificio" in it
