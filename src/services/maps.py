from src.models import MapPoint


class MapService:
    def points_in_bbox(self, south, west, north, east, filters, cap=5000):
        qs = MapPoint.objects.filter(lat__gte=south, lat__lte=north, lon__gte=west, lon__lte=east)
        if filters.get("canton"):
            qs = qs.filter(canton=filters["canton"])
        if filters.get("gkat"):
            qs = qs.filter(gkat=filters["gkat"])
        if filters.get("genh1"):
            qs = qs.filter(genh1=filters["genh1"])
        rows = list(qs.values("egid", "lat", "lon")[: cap + 1])
        truncated = len(rows) > cap
        rows = rows[:cap]
        features = [
            {
                "type": "Feature",
                # GeoJSON coordinate order is [lon, lat] — not [lat, lon].
                "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                "properties": {"egid": r["egid"]},
            }
            for r in rows
        ]
        return {"type": "FeatureCollection", "features": features, "truncated": truncated}
