from django.db.models import Count

from src.models import Building
from src.services.labels import LabelService


class FacetService:
    """Filters and aggregates `Building` rows directly.

    GDEKT/GKAT/GBAUJ/GENH1 are indexed columns on the single Postgres
    `building` table, so both the filtered page of results and the facet
    counts are computed straight off it — no sidecar table needed.
    """

    def __init__(self) -> None:
        self._labels = LabelService()

    def _qs(self, canton, gkat, year_from, year_to, genh1):
        qs = Building.objects.all()
        if canton:
            qs = qs.filter(GDEKT=canton)
        if gkat:
            qs = qs.filter(GKAT=gkat)
        if genh1:
            qs = qs.filter(GENH1=genh1)
        if year_from:
            qs = qs.filter(GBAUJ__gte=year_from)
        if year_to:
            qs = qs.filter(GBAUJ__lte=year_to)
        return qs

    def query(self, canton=None, gkat=None, year_from=None, year_to=None, genh1=None, page=1, page_size=25):
        qs = self._qs(canton, gkat, year_from, year_to, genh1)
        count = qs.count()
        start = (page - 1) * page_size
        results = list(qs.order_by("EGID")[start : start + page_size])
        return {
            "count": count,
            "results": results,
            "page": page,
            "has_next": start + page_size < count,
            "has_previous": page > 1,
            "next_page": page + 1,
            "previous_page": page - 1,
            "facets": self._facets(qs),
        }

    def _facets(self, qs):
        def opts(field, merkmal):
            out = [
                {
                    "key": r[field],
                    "label": self._labels.value(merkmal, r[field]) if r[field] else "unbekannt",
                    "count": r["n"],
                }
                for r in qs.values(field).annotate(n=Count("EGID"))
            ]
            return sorted(out, key=lambda o: -o["count"])

        canton = sorted(
            (
                {"key": r["GDEKT"], "label": r["GDEKT"] or "unbekannt", "count": r["n"]}
                for r in qs.values("GDEKT").annotate(n=Count("EGID"))
            ),
            key=lambda o: -o["count"],
        )
        return {"canton": canton, "gkat": opts("GKAT", "GKAT"), "genh1": opts("GENH1", "GENH1")}
