import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_search_by_street_returns_egid():
    from src.services.search import SearchService

    call_command("build_index", "--only", "search")
    hits = SearchService().search("Grossholzerstrasse")
    assert any(h["egid"] == 1 for h in hits)


def test_search_by_egid():
    from src.services.search import SearchService

    call_command("build_index", "--only", "search")
    hits = SearchService().search("1")
    assert any(h["egid"] == 1 for h in hits)


def test_search_with_no_word_characters_returns_empty():
    from src.services.search import SearchService

    call_command("build_index", "--only", "search")
    assert SearchService().search("!!!") == []


def test_search_results_view_renders(client):
    call_command("build_index", "--only", "search")
    resp = client.get("/suche/", {"q": "Grossholzerstrasse"})
    assert resp.status_code == 200
    assert b"/gebaeude/1/" in resp.content
