import zipfile

from tests.make_csv_fixture import BUILDINGS, CODES, DWELLINGS, ENTRANCES, SAMPLE_ZIP


def test_sample_zip_has_four_csvs():
    assert SAMPLE_ZIP.exists()
    with zipfile.ZipFile(SAMPLE_ZIP) as zf:
        names = set(zf.namelist())
    assert {BUILDINGS, ENTRANCES, DWELLINGS, CODES} <= names
