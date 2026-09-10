from django.http import Http404
from django.shortcuts import render

from src.models import Building, Dwelling, Entrance
from src.services.facets import FacetService
from src.services.labels import LabelService
from src.services.search import SearchService
from src.services.stats import StatsService

_DASHBOARD_METRICS = [
    ("buildings_by_canton", "Gebäude pro Kanton"),
    ("buildings_by_decade", "Gebäude nach Baujahrzehnt"),
    ("buildings_by_category", "Gebäudekategorie"),
    ("heating_energy", "Energie-/Wärmequelle Heizung"),
    ("dwellings_by_rooms", "Wohnungen nach Zimmerzahl"),
    ("building_status", "Gebäudestatus"),
]

# (column, coded-field name or None for a raw/free-text value)
_BUILDING_FIELDS = [
    ("GGDENAME", None),
    ("GDEKT", None),
    ("GBAUJ", None),
    ("GKAT", "GKAT"),
    ("GKLAS", "GKLAS"),
    ("GSTAT", "GSTAT"),
    ("GAREA", None),
    ("GVOL", None),
    ("GASTW", None),
    ("GANZWHG", None),
    ("GENH1", "GENH1"),
]


def search(request):
    return render(request, "search.html")


def search_results(request):
    hits = SearchService().search(request.GET.get("q", ""))
    return render(request, "partials/search_results.html", {"hits": hits})


def building_detail(request, egid: int):
    try:
        b = Building.objects.using("gwr").get(EGID=egid)
    except Building.DoesNotExist as exc:
        raise Http404("Unbekannte EGID") from exc
    labels = LabelService()
    attrs = []
    for col, merkmal in _BUILDING_FIELDS:
        raw = getattr(b, col)
        value = labels.value(merkmal, raw) if merkmal else raw
        attrs.append({"col": col, "label": labels.field(col), "value": value})
    entrances = list(Entrance.objects.using("gwr").filter(EGID=egid))
    dwellings = list(Dwelling.objects.using("gwr").filter(EGID=egid))
    # Precomputed here (not in the template) because Django templates can't
    # call labels.value(merkmal, code) with two arguments.
    dwelling_rows = [
        {
            "floor": labels.value("WSTWK", d.WSTWK),
            "rooms": d.WAZIM,
            "area": d.WAREA,
            "status": labels.value("WSTAT", d.WSTAT),
        }
        for d in dwellings
    ]
    return render(
        request,
        "building_detail.html",
        {
            "b": b,
            "attrs": attrs,
            "entrances": entrances,
            "dwellings": dwellings,
            "dwelling_rows": dwelling_rows,
        },
    )


def _facet_params(request):
    """Parse and validate facet query params from the request's GET dict."""
    g = request.GET

    def _int(name):
        v = g.get(name)
        return int(v) if v and v.isdigit() else None

    return {
        "canton": g.get("canton") or None,
        "gkat": _int("gkat"),
        "genh1": _int("genh1"),
        "year_from": _int("year_from"),
        "year_to": _int("year_to"),
        "page": _int("page") or 1,
    }


def explorer(request):
    data = FacetService().query(**_facet_params(request))
    return render(request, "explorer.html", data)


def explorer_results(request):
    data = FacetService().query(**_facet_params(request))
    return render(request, "partials/explorer_results.html", data)


def stats(request):
    svc = StatsService()
    charts = [{"metric": m, "title": t, "rows": svc.metric(m)} for m, t in _DASHBOARD_METRICS]
    return render(request, "stats.html", {"charts": charts})
