from django.http import JsonResponse

from src.services.stats import StatsService


def stats_json(request, metric: str):
    data = StatsService().metric(metric)
    return JsonResponse({"labels": [d["label"] for d in data], "values": [d["value"] for d in data]})
