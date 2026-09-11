from django.db import connection
from django.utils.translation import gettext, get_language

from src.services.labels import LabelService

_CODE_METRIC = {"buildings_by_category": "GKAT", "building_status": "GSTAT", "heating_energy": "GENH1"}


class StatsService:
    """Resolves mv_stats raw dim_key values into speaking labels for the active language."""

    def __init__(self) -> None:
        self._labels = LabelService()

    def metric(self, name: str) -> list[dict]:
        with connection.cursor() as cur:
            cur.execute("SELECT dim_key, value FROM mv_stats WHERE metric = %s ORDER BY value DESC", (name,))
            rows = cur.fetchall()
        return [{"key": k, "label": self._label(name, k), "value": v} for k, v in rows]

    def _label(self, metric: str, key: str | None) -> str:
        if key in ("", None):
            return gettext("unbekannt")
        if metric in _CODE_METRIC:
            try:
                return self._labels.value(_CODE_METRIC[metric], int(key))
            except (TypeError, ValueError):
                return str(key)
        if metric == "buildings_by_decade":
            suffix = "er" if (get_language() or "de") == "de" else ""
            return f"{key}{suffix}"
        if metric == "dwellings_by_rooms":
            return f"{key} {gettext('Zimmer')}"
        return str(key)  # buildings_by_canton (abbrev as-is)
