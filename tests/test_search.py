import pytest
from django.core.management import call_command

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def _import():
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))


def test_search_by_street():
    _import()
    from src.services.search import SearchService

    hits = SearchService().search("Grossholzerstrasse")
    assert any(h["egid"] == 1 for h in hits)


def test_search_by_egid():
    _import()
    from src.services.search import SearchService

    assert any(h["egid"] == 1 for h in SearchService().search("1"))


def test_search_fuzzy_typo():
    _import()
    from src.services.search import SearchService

    # one-letter typo still finds the street via trigram fallback
    hits = SearchService().search("Grossholzerstrase")
    assert any(h["egid"] == 1 for h in hits)


def test_search_punctuation_only_is_empty():
    _import()
    from src.services.search import SearchService

    assert SearchService().search("!!!") == []
