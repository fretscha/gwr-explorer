from functools import lru_cache

from pyproj import Transformer


class CoordTransform:
    """Reproject Swiss LV95 (EPSG:2056) to WGS84 (EPSG:4326)."""

    def __init__(self) -> None:
        self._t = _transformer()

    def to_wgs84(self, easting: float, northing: float) -> tuple[float, float]:
        lon, lat = self._t.transform(easting, northing)
        return lat, lon


@lru_cache(maxsize=1)
def _transformer() -> Transformer:
    return Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
