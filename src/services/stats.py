from src.models import StatsCache


class StatsService:
    def metric(self, name: str) -> list[dict]:
        rows = StatsCache.objects.filter(metric=name).order_by("-value")
        return [{"key": r.dim_key, "label": r.dim_label, "value": r.value} for r in rows]
