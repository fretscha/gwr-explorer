import json

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db(databases=["default", "gwr"], transaction=True)


def test_stats_service_metric():
    from src.services.stats import StatsService

    call_command("build_index", "--only", "stats")
    data = StatsService().metric("buildings_by_canton")
    assert data and {"key", "label", "value"} <= set(data[0])


def test_stats_api_endpoint(client):
    call_command("build_index", "--only", "stats")
    resp = client.get("/api/stats/heating_energy/")
    assert resp.status_code == 200
    payload = json.loads(resp.content)
    assert "labels" in payload and "values" in payload
    assert len(payload["labels"]) == len(payload["values"])
