class StatsService:
    def metric(self, name: str) -> list[dict]:
        # Deferred import: StatsCache is a v1 sidecar model slated for removal in
        # a later re-platform task; a module-level import would break Django's
        # urlconf-loading system checks now that src.models no longer exports it.
        from src.models import StatsCache

        rows = StatsCache.objects.filter(metric=name).order_by("-value")
        return [{"key": r.dim_key, "label": r.dim_label, "value": r.value} for r in rows]
