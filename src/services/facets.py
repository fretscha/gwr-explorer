from django.db.models import Count

from src.models import Building, MapPoint
from src.services.labels import LabelService


class FacetService:
    """Combines canton / building category / build-year / heating-type facets.

    Counts and filtering run against the small, indexed `MapPoint` sidecar
    table (fast for aggregation); the returned page of result rows is then
    fetched from the authoritative `Building` table on the read-only `gwr`
    database, keyed by the EGIDs of the matching MapPoints.
    """

    def __init__(self) -> None:
        self._labels = LabelService()

    def _filtered_points(self, canton, gkat, year_from, year_to, genh1):
        qs = MapPoint.objects.all()
        if canton:
            qs = qs.filter(canton=canton)
        if gkat:
            qs = qs.filter(gkat=gkat)
        if genh1:
            qs = qs.filter(genh1=genh1)
        if year_from:
            qs = qs.filter(gbauj__gte=year_from)
        if year_to:
            qs = qs.filter(gbauj__lte=year_to)
        return qs

    def query(self, canton=None, gkat=None, year_from=None, year_to=None, genh1=None, page=1, page_size=25):
        points = self._filtered_points(canton, gkat, year_from, year_to, genh1)
        count = points.count()
        start = (page - 1) * page_size
        egids = list(points.order_by("egid").values_list("egid", flat=True)[start : start + page_size])
        results = list(Building.objects.using("gwr").filter(EGID__in=egids).order_by("EGID"))
        has_next = start + page_size < count
        return {
            "count": count,
            "results": results,
            "page": page,
            "has_next": has_next,
            "has_previous": page > 1,
            "next_page": page + 1,
            "previous_page": page - 1,
            "facets": self._facets(points),
        }

    def _facets(self, points):
        def opts(field, merkmal):
            out = []
            for r in points.values(field).annotate(n=Count("id")):
                code = r[field]
                label = self._labels.value(merkmal, code) if code else "unbekannt"
                out.append({"key": code, "label": label, "count": r["n"]})
            return sorted(out, key=lambda o: -o["count"])

        canton_opts = [
            {"key": r["canton"], "label": r["canton"] or "unbekannt", "count": r["n"]}
            for r in points.values("canton").annotate(n=Count("id"))
        ]
        return {
            "canton": sorted(canton_opts, key=lambda o: -o["count"]),
            "gkat": opts("gkat", "GKAT"),
            "genh1": opts("genh1", "GENH1"),
        }
