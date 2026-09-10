import logging

from django.core.management.base import BaseCommand
from django.db import connections

from src.models import Building, Entrance, MapPoint
from src.utils.coords import CoordTransform

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "(Re)build the sidecar search/map/stats artifacts from the read-only GWR source."

    def add_arguments(self, parser):
        parser.add_argument("--only", choices=["search", "map", "stats"], default=None)
        parser.add_argument("--limit", type=int, default=None, help="Limit source rows (for dev).")

    def handle(self, *args, **opts):
        only = opts["only"]
        if only in (None, "search"):
            self._build_search(opts["limit"])
        if only in (None, "map"):
            self._build_map(opts["limit"])
        # stats step is added in Task 8
        self.stdout.write(self.style.SUCCESS("build_index complete"))

    def _build_search(self, limit):
        conn = connections["default"]
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS search_entrance")
            cur.execute(
                "CREATE VIRTUAL TABLE search_entrance USING fts5("
                "label, canton UNINDEXED, egid UNINDEXED, tokenize='unicode61')"
            )
            qs = Entrance.objects.using("gwr").exclude(STRNAME__isnull=True)
            if limit:
                qs = qs[:limit]
            batch = []
            for e in qs.iterator(chunk_size=5000):
                label = " ".join(str(p) for p in [e.STRNAME, e.DEINR, e.DPLZ4, e.DPLZNAME] if p)
                batch.append((label, None, e.EGID))
                if len(batch) >= 5000:
                    cur.executemany("INSERT INTO search_entrance(label,canton,egid) VALUES (?,?,?)", batch)
                    batch.clear()
            if batch:
                cur.executemany("INSERT INTO search_entrance(label,canton,egid) VALUES (?,?,?)", batch)
        logger.info("search_entrance built")

    def _build_map(self, limit):
        MapPoint.objects.all().delete()
        transform = CoordTransform()
        qs = Building.objects.using("gwr").exclude(GKODE__isnull=True).exclude(GKODN__isnull=True)
        if limit:
            qs = qs[:limit]
        batch = []
        for b in qs.iterator(chunk_size=5000):
            lat, lon = transform.to_wgs84(b.GKODE, b.GKODN)
            batch.append(MapPoint(egid=b.EGID, lat=lat, lon=lon, canton=b.GDEKT, gkat=b.GKAT, gbauj=b.GBAUJ, genh1=b.GENH1))
            if len(batch) >= 5000:
                MapPoint.objects.bulk_create(batch)
                batch.clear()
        if batch:
            MapPoint.objects.bulk_create(batch)
        logger.info("map_point built")
