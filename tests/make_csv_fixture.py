"""Build tests/fixtures/ch_sample.zip: the 4 GWR CSVs sampled to N buildings.

Usage: uv run python tests/make_csv_fixture.py /path/to/ch.zip
Streams each big TSV, keeps header + rows whose EGID is in the first N buildings
(+ all code rows), writes a small zip with the same 4 filenames.
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

SAMPLE_ZIP = Path(__file__).parent / "fixtures" / "ch_sample.zip"
N_BUILDINGS = 500
BUILDINGS = "gebaeude_batiment_edificio.csv"
ENTRANCES = "eingang_entree_entrata.csv"
DWELLINGS = "wohnung_logement_abitazione.csv"
CODES = "kodes_codes_codici.csv"


def _rows(zf, name):
    with zf.open(name) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
        reader = csv.reader(text, delimiter="\t")
        header = next(reader)
        yield header
        yield from reader


def build(src_zip: str) -> None:
    SAMPLE_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src_zip) as zf:
        brows = list(_rows(zf, BUILDINGS))
        bheader, bdata = brows[0], brows[1 : 1 + N_BUILDINGS]
        egids = {r[0] for r in bdata}

        def filtered(name):
            it = _rows(zf, name)
            header = next(it)
            keep = [r for r in it if r and r[0] in egids]
            return header, keep

        eheader, edata = filtered(ENTRANCES)
        dheader, ddata = filtered(DWELLINGS)
        cheader = next(_rows(zf, CODES))
        cdata = [r for r in list(_rows(zf, CODES))[1:]]

    def write_tsv(zout, name, header, data):
        buf = io.StringIO(newline="")
        w = csv.writer(buf, delimiter="\t", lineterminator="\r\n")
        w.writerow(header)
        w.writerows(data)
        zout.writestr(name, buf.getvalue().encode("utf-8"))

    if SAMPLE_ZIP.exists():
        SAMPLE_ZIP.unlink()
    with zipfile.ZipFile(SAMPLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zout:
        write_tsv(zout, BUILDINGS, bheader, bdata)
        write_tsv(zout, ENTRANCES, eheader, edata)
        write_tsv(zout, DWELLINGS, dheader, ddata)
        write_tsv(zout, CODES, cheader, cdata)
    print(f"Wrote {SAMPLE_ZIP} ({SAMPLE_ZIP.stat().st_size} bytes), {len(bdata)} buildings")


if __name__ == "__main__":
    build(sys.argv[1])
