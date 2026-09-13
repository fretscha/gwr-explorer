from django.http import JsonResponse

from src.services.maps import MapService
from src.services.stats import StatsService


def stats_json(request, metric: str):
    data = StatsService().metric(metric)
    return JsonResponse({"labels": [d["label"] for d in data], "values": [d["value"] for d in data]})


def _int_param(request, name):
    v = request.GET.get(name)
    return int(v) if v and v.isdigit() else None


# The map only draws objects once the viewport holds fewer than the selected
# threshold; the user zooms in until that many remain. The threshold is picked
# from a fixed whitelist (the UI offers exactly these) so a crafted ?limit= can't
# demand an unbounded result set. cap = limit - 1 means the limit-th match trips
# `truncated`, and we ship no features so the client shows a "zoom in" hint rather
# than a dense, unreadable blob.
MAP_POINT_LIMITS = (250, 500, 1000)
DEFAULT_MAP_POINT_LIMIT = 250


def map_points(request):
    g = request.GET
    try:
        # Required bbox params: missing (KeyError) or non-numeric (ValueError) client
        # input must yield a 400, not an uncaught exception -> raw 500.
        south, west, north, east = (float(g["south"]), float(g["west"]), float(g["north"]), float(g["east"]))
    except (KeyError, ValueError):
        return JsonResponse({"error": "Ungültige oder fehlende bbox-Parameter (south/west/north/east)"}, status=400)
    limit = _int_param(request, "limit")
    if limit not in MAP_POINT_LIMITS:
        limit = DEFAULT_MAP_POINT_LIMIT
    filters = {
        "canton": g.get("canton"),
        "gkat": _int_param(request, "gkat"),
        "genh1": _int_param(request, "genh1"),
    }
    svc = MapService()
    fc = svc.points_in_bbox(south, west, north, east, filters, cap=limit - 1)
    # At or above the threshold the client draws no per-building circles; instead of
    # the discarded points it gets a density grid to render as a heatmap overview.
    if fc["truncated"]:
        fc["features"] = []
        fc["density"] = svc.density_in_bbox(south, west, north, east, filters)["cells"]
    return JsonResponse(fc)
