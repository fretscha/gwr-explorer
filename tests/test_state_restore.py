"""Search and Explorer restore their selection from the URL query string, so a
full-page reload (e.g. a language switch) keeps the user's context."""
import pytest
from django.core.management import call_command
from django.urls import reverse

from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_search_page_restores_query_and_results(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    resp = client.get(reverse("gwr:search") + "?q=Grossholzerstrasse")
    assert resp.status_code == 200
    html = resp.content.decode()
    # The search box is pre-filled with the query...
    assert 'value="Grossholzerstrasse"' in html
    # ...and the matching building is rendered inline (not only via a later HTMX
    # fetch), so a reload shows the results immediately.
    assert reverse("gwr:building_detail", args=[1]) in html


def test_search_page_without_query_has_empty_box(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    resp = client.get(reverse("gwr:search"))
    assert resp.status_code == 200
    assert 'value=""' in resp.content.decode()


def test_explorer_preselects_filters_from_url(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    resp = client.get(reverse("gwr:explorer") + "?year_from=1990&year_to=2000")
    assert resp.status_code == 200
    html = resp.content.decode()
    assert 'name="year_from"' in html and 'value="1990"' in html
    assert 'name="year_to"' in html and 'value="2000"' in html
