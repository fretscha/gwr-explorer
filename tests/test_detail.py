import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.urls import reverse

from gwr.models import Building, Entrance
from tests.make_csv_fixture import SAMPLE_ZIP

pytestmark = pytest.mark.django_db(transaction=True)


def test_detail_speaking_labels(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    resp = client.get(reverse("gwr:building_detail", args=[1]))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Gebäudekategorie" in body and "Baujahr des Gebäudes" in body
    assert "GKAT" not in body.split("title=")[0]


def test_detail_404(client):
    call_command("import_gwr", "--file", str(SAMPLE_ZIP))
    assert client.get(reverse("gwr:building_detail", args=[99999999])).status_code == 404


@pytest.mark.django_db
def test_detail_dedups_bilingual_entrance_by_egid_edid(client):
    # Bilingual communes repeat the same physical entrance (EGID, EDID) with
    # a different STRNAME per language (e.g. "Rue de la Gare" vs "Bahnhofstrasse").
    # De-dup must key on (EGID, EDID), not on the address text, or both
    # language rows survive and the entrance renders twice.
    egid = 90000001
    Building.objects.create(EGID=egid, GDEKT="FR", geom=Point(2600000, 1200000, srid=2056))
    Entrance.objects.create(
        EGID=egid,
        EDID=1,
        STRNAME="Bahnhofstrasse",
        STRSP=1,
        STROFFIZIEL=1,
        DEINR="5",
        DPLZ4=1700,
        DPLZNAME="Fribourg",
        address_label="Bahnhofstrasse 5",
    )
    Entrance.objects.create(
        EGID=egid,
        EDID=1,
        STRNAME="Rue de la Gare",
        STRSP=2,
        STROFFIZIEL=0,
        DEINR="5",
        DPLZ4=1700,
        DPLZNAME="Fribourg",
        address_label="Rue de la Gare 5",
    )

    resp = client.get(reverse("gwr:building_detail", args=[egid]))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert body.count("<li>") == 1
    assert "Bahnhofstrasse" in body
    assert "Rue de la Gare" not in body
