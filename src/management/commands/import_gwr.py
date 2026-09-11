"""Import the GWR CSV export (ch.zip) into PostgreSQL/PostGIS.

Pipeline: obtain ch.zip (local --file or download --url) -> inside ONE
transaction, COPY each of the 4 TSVs into an all-text UNLOGGED staging table,
then TRUNCATE + INSERT...SELECT with casts into the typed model tables,
building geometry (LV95 / EPSG:2056) for buildings and entrances along the
way. Staging tables are dropped at the end. Re-running replaces all data
(truncate + reload), so the command is idempotent.
"""

import io
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

BUILDINGS = "gebaeude_batiment_edificio.csv"
ENTRANCES = "eingang_entree_entrata.csv"
DWELLINGS = "wohnung_logement_abitazione.csv"
CODES = "kodes_codes_codici.csv"

# CSV column -> staging table column (all TEXT; casts applied in _transform).
BUILDING_COLS = [
    "EGID", "GDEKT", "GGDENR", "GGDENAME", "EGRID", "LGBKR", "LPARZ", "LPARZSX", "LTYP",
    "GEBNR", "GBEZ", "GKODE", "GKODN", "GKSCE", "GSTAT", "GKAT", "GKLAS", "GBAUJ", "GBAUM",
    "GBAUP", "GABBJ", "GAREA", "GVOL", "GVOLNORM", "GVOLSCE", "GASTW", "GANZWHG", "GAZZI",
    "GSCHUTZR", "GEBF", "GWAERZH1", "GENH1", "GWAERSCEH1", "GWAERDATH1", "GWAERZH2", "GENH2",
    "GWAERSCEH2", "GWAERDATH2", "GWAERZW1", "GENW1", "GWAERSCEW1", "GWAERDATW1", "GWAERZW2",
    "GENW2", "GWAERSCEW2", "GWAERDATW2", "GEXPDAT",
]
ENTRANCE_COLS = [
    "EGID", "EDID", "EGAID", "DEINR", "ESID", "STRNAME", "STRNAMK", "STRINDX", "STRSP",
    "STROFFIZIEL", "DPLZ4", "DPLZZ", "DPLZNAME", "DKODE", "DKODN", "DOFFADR", "DEXPDAT",
]
DWELLING_COLS = [
    "EGID", "EWID", "EDID", "WHGNR", "WEINR", "WSTWK", "WBEZ", "WMEHRG", "WBAUJ", "WABBJ",
    "WSTAT", "WAREA", "WAZIM", "WKCHE", "WEXPDAT",
]
CODE_COLS = ["CECODID", "CMERKM", "CODTXTLD", "CODTXTKD", "CODTXTLF", "CODTXTKF", "CODTXTLI", "CODTXTKI", "CEXPDAT"]


def _n(col):
    """NULLIF("col",'') — staging columns are TEXT; an empty string (not NULL)
    would otherwise blow up any ::int / ::float8 cast."""
    return f"NULLIF(\"{col}\",'')"


class Command(BaseCommand):
    help = "Import the GWR CSV export (ch.zip) into PostgreSQL/PostGIS."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=None, help="Local ch.zip (skip download).")
        parser.add_argument("--url", default=settings.GWR_ZIP_URL)
        parser.add_argument("--skip-download", action="store_true")
        parser.add_argument("--limit", type=int, default=None, help="Limit rows per CSV (for dev).")

    def handle(self, *args, **opts):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = self._obtain(opts, Path(tmp))
            with zipfile.ZipFile(zip_path) as zf, transaction.atomic():
                self._load(zf, BUILDINGS, "stg_building", BUILDING_COLS, opts["limit"])
                self._load(zf, ENTRANCES, "stg_entrance", ENTRANCE_COLS, opts["limit"])
                self._load(zf, DWELLINGS, "stg_dwelling", DWELLING_COLS, opts["limit"])
                self._load(zf, CODES, "stg_code", CODE_COLS, None)
                self._transform()
        self.stdout.write(self.style.SUCCESS("import_gwr complete"))

    def _obtain(self, opts, tmp):
        if opts["file"]:
            return opts["file"]
        if opts["skip_download"]:
            raise CommandError("--skip-download requires --file")
        dest = tmp / "ch.zip"
        self.stdout.write(f"Downloading {opts['url']} ...")
        urllib.request.urlretrieve(opts["url"], dest)  # noqa: S310 (trusted BFS URL)
        return dest

    def _load(self, zf, csv_name, staging, cols, limit):
        """COPY the TSV into an all-text staging table via psycopg COPY."""
        with connection.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {staging}")
            coldefs = ", ".join(f'"{c}" text' for c in cols)
            cur.execute(f"CREATE UNLOGGED TABLE {staging} ({coldefs})")
            collist = ", ".join(f'"{c}"' for c in cols)
            copy_sql = (
                f"COPY {staging} ({collist}) FROM STDIN "
                "WITH (FORMAT csv, DELIMITER E'\\t', HEADER true, NULL '')"
            )
            with zf.open(csv_name) as fh, cur.copy(copy_sql) as copy:
                if limit is None:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        copy.write(chunk)
                else:
                    self._copy_limited(fh, copy, limit)

    def _copy_limited(self, fh, copy, limit):
        text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
        header = text.readline()
        copy.write(header.encode("utf-8"))
        for i, line in enumerate(text):
            if i >= limit:
                break
            copy.write(line.encode("utf-8"))

    def _transform(self):
        """Cast staging text -> typed model tables; build geometry + address_label."""
        with connection.cursor() as cur:
            cur.execute("TRUNCATE building, entrance, dwelling, code RESTART IDENTITY CASCADE")

            # code
            cur.execute(
                'INSERT INTO code ("CECODID","CMERKM","CODTXTLD","CODTXTLF","CODTXTLI") '
                f'SELECT {_n("CECODID")}::int, "CMERKM", "CODTXTLD", "CODTXTLF", "CODTXTLI" '
                "FROM stg_code"
            )

            # building (+ geom)
            cur.execute(
                'INSERT INTO building ("EGID","GDEKT","GGDENR","GGDENAME","GKODE","GKODN",'
                '"GSTAT","GKAT","GKLAS","GBAUJ","GBAUP","GAREA","GVOL","GASTW","GANZWHG",'
                '"GENH1","GENH2", geom) '
                f'SELECT {_n("EGID")}::int, "GDEKT", {_n("GGDENR")}::int, "GGDENAME", '
                f'{_n("GKODE")}::float8, {_n("GKODN")}::float8, '
                f'{_n("GSTAT")}::int, {_n("GKAT")}::int, {_n("GKLAS")}::int, {_n("GBAUJ")}::int, '
                f'{_n("GBAUP")}::int, {_n("GAREA")}::int, {_n("GVOL")}::int, {_n("GASTW")}::int, '
                f'{_n("GANZWHG")}::int, {_n("GENH1")}::int, {_n("GENH2")}::int, '
                f'CASE WHEN {_n("GKODE")} IS NOT NULL AND {_n("GKODN")} IS NOT NULL '
                f'THEN ST_SetSRID(ST_MakePoint({_n("GKODE")}::float8, {_n("GKODN")}::float8), 2056) END '
                "FROM stg_building"
            )

            # entrance (+ geom, address_label) -- keep ALL rows (bilingual duplicates)
            cur.execute(
                'INSERT INTO entrance ("EGID","EDID","STRNAME","STRSP","STROFFIZIEL","DEINR",'
                '"DPLZ4","DPLZNAME","DKODE","DKODN", address_label, geom) '
                f'SELECT {_n("EGID")}::int, {_n("EDID")}::int, "STRNAME", {_n("STRSP")}::int, '
                f'{_n("STROFFIZIEL")}::int, "DEINR", {_n("DPLZ4")}::int, "DPLZNAME", '
                f'{_n("DKODE")}::float8, {_n("DKODN")}::float8, '
                "concat_ws(' ', \"STRNAME\", \"DEINR\", \"DPLZ4\", \"DPLZNAME\"), "
                f'CASE WHEN {_n("DKODE")} IS NOT NULL AND {_n("DKODN")} IS NOT NULL '
                f'THEN ST_SetSRID(ST_MakePoint({_n("DKODE")}::float8, {_n("DKODN")}::float8), 2056) END '
                "FROM stg_entrance"
            )
            cur.execute("UPDATE entrance SET search_vector = to_tsvector('simple', coalesce(address_label,''))")

            # dwelling
            cur.execute(
                'INSERT INTO dwelling ("EGID","EWID","EDID","WSTWK","WBEZ","WSTAT","WAREA",'
                '"WAZIM","WKCHE","WBAUJ") '
                f'SELECT {_n("EGID")}::int, {_n("EWID")}::int, {_n("EDID")}::int, {_n("WSTWK")}::int, '
                f'"WBEZ", {_n("WSTAT")}::int, {_n("WAREA")}::int, {_n("WAZIM")}::int, '
                f'{_n("WKCHE")}::int, {_n("WBAUJ")}::int '
                "FROM stg_dwelling"
            )

            for stg in ("stg_building", "stg_entrance", "stg_dwelling", "stg_code"):
                cur.execute(f"DROP TABLE IF EXISTS {stg}")
