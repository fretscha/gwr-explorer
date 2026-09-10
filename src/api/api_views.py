from django.http import JsonResponse

from src.services.maps import MapService
from src.services.stats import StatsService


def stats_json(request, metric: str):
    data = StatsService().metric(metric)
    return JsonResponse({"labels": [d["label"] for d in data], "values": [d["value"] for d in data]})


def _int_param(request, name):
    v = request.GET.get(name)
    return int(v) if v and v.isdigit() else None


def map_points(request):
    g = request.GET
    try:
        # Required bbox params: missing (KeyError) or non-numeric (ValueError) client
        # input must yield a 400, not an uncaught exception -> raw 500.
        south, west, north, east = (float(g["south"]), float(g["west"]), float(g["north"]), float(g["east"]))
    except (KeyError, ValueError):
        return JsonResponse({"error": "Ungültige oder fehlende bbox-Parameter (south/west/north/east)"}, status=400)
    fc = MapService().points_in_bbox(
        south,
        west,
        north,
        east,
        {
            "canton": g.get("canton"),
            "gkat": _int_param(request, "gkat"),
            "genh1": _int_param(request, "genh1"),
        },
    )
    return JsonResponse(fc)
