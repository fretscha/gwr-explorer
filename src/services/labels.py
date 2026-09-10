import logging

from src.models import Code
from src.utils.field_labels import field_label

logger = logging.getLogger(__name__)


class LabelService:
    """Resolves cryptic field names and coded values to speaking German text."""

    def __init__(self, code_queryset=None) -> None:
        self._map: dict[tuple[str, int], str] = {}
        try:
            rows = code_queryset if code_queryset is not None else Code.objects.using("gwr").all()
            for row in rows:
                self._map[(row.CMERKM, row.CECODID)] = row.CODTXTLD
        except Exception:  # pragma: no cover - defensive; logged for debugging
            logger.exception("Failed to load code table")
            raise

    def field(self, name: str) -> str:
        return field_label(name)

    def value(self, merkmal: str, code: int | None) -> str:
        if code is None:
            return ""
        return self._map.get((merkmal, code), str(code))
