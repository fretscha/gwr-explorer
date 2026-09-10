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
    fc = MapService().points_in_bbox(
        float(g["south"]),
        float(g["west"]),
        float(g["north"]),
        float(g["east"]),
        {
            "canton": g.get("canton"),
            "gkat": _int_param(request, "gkat"),
            "genh1": _int_param(request, "genh1"),
        },
    )
    return JsonResponse(fc)
