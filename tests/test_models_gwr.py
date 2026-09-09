import pytest

pytestmark = pytest.mark.django_db(databases=["gwr"])


def test_building_rows_readable():
    from src.models import Building

    assert Building.objects.using("gwr").count() == 500
    b = Building.objects.using("gwr").order_by("EGID").first()
    assert b.EGID == 1
    assert b.GGDENAME

    # Verified defect fix: entrance/dwelling/code have no `id` column and are
    # composite-pk rowid tables, not rowid-alias tables like building. Reading
    # them requires the IntegerField(primary_key=True, db_column="rowid") pk
    # override rather than the brief's AutoField(pk) which would generate
    # "SELECT ... id ..." and fail with "no such column: id".
    from src.models import Code, Dwelling, Entrance

    assert Entrance.objects.using("gwr").filter(EGID=1).exists()
    assert Dwelling.objects.using("gwr").filter(EGID=1).count() >= 1
    assert Code.objects.using("gwr").filter(CMERKM="GKAT").exists()
