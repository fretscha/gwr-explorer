from django.db import connection


class MapService:
    @staticmethod
    def _filter_clauses(filters):
        """(sql, value) pairs for the optional canton/gkat/genh1 facet filters."""
        cols = [("canton", '"GDEKT" = %s'), ("gkat", '"GKAT" = %s'), ("genh1", '"GENH1" = %s')]
        return [(clause, filters[key]) for key, clause in cols if filters.get(key)]

    def points_in_bbox(self, south, west, north, east, filters, cap=5000):
        # geom is stored in the Swiss LV95 (EPSG:2056) CRS; the incoming bbox is
        # WGS84 (lon/lat), so the envelope is reprojected to 2056 before the &&
        # index-assisted intersection test, then results are reprojected back to
        # 4326 for GeoJSON output ([lon, lat] order).
        #
        # ST_Transform of a raw 4-corner envelope is only linear-ish over small
        # areas: a coarse rectangle (e.g. a world-spanning bbox) can reproject to a
        # degenerate/collapsed polygon because the projection is non-linear between
        # the corners. ST_Segmentize adds intermediate vertices along the edges
        # first so the reprojected shape's envelope faithfully covers the source
        # rectangle at any scale.
        where = [
            "geom IS NOT NULL",
            "geom && ST_Transform(ST_Segmentize(ST_MakeEnvelope(%s, %s, %s, %s, 4326), 1), 2056)",
        ]
        params = [west, south, east, north]
        for clause, val in self._filter_clauses(filters):
            where.append(clause)
            params.append(val)
        # The `&&` test above is still a fast GiST-index prefilter on bounding
        # envelopes, not an exact clip: even the segmentized reprojection's envelope
        # can bulge slightly beyond the true image of the rectangle. That can admit
        # a handful of points just outside the requested bbox, so re-check exact
        # bounds in WGS84 after transforming back, before applying the cap.
        # GENH1 (heating method → circle colour) and GEBF (Energiebezugsfläche /
        # heated surface m² → circle size) travel with each point so the map can
        # render coloured, size-scaled circles without a per-point round-trip.
        sql = (
            'SELECT "EGID", lon, lat, "GENH1", "GEBF" FROM ('
            'SELECT "EGID", "GENH1", "GEBF", '
            "ST_X(ST_Transform(geom, 4326)) AS lon, ST_Y(ST_Transform(geom, 4326)) AS lat "
            "FROM building WHERE " + " AND ".join(where) + ") s "
            "WHERE lon BETWEEN %s AND %s AND lat BETWEEN %s AND %s "
            "LIMIT %s"
        )
        params.extend([west, east, south, north, cap + 1])
        with connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        truncated = len(rows) > cap
        rows = rows[:cap]
        features = [
            {
                "type": "Feature",
                # GeoJSON coordinate order is [lon, lat] — not [lat, lon].
                "geometry": {"type": "Point", "coordinates": [r[1], r[2]]},
                "properties": {"egid": r[0], "genh1": r[3], "gebf": r[4]},
            }
            for r in rows
        ]
        return {"type": "FeatureCollection", "features": features, "truncated": truncated}

    def density_in_bbox(self, south, west, north, east, filters, cols=64):
        """Aggregate buildings into a grid for a heatmap overview when a viewport
        holds too many to draw individually.

        Snapping happens in LV95 (EPSG:2056) metres so cells are square on the
        ground, and only the (few thousand) resulting cell corners are
        reprojected to WGS84 — far cheaper than transforming every point.
        """
        env = "ST_Transform(ST_Segmentize(ST_MakeEnvelope(%s, %s, %s, %s, 4326), 1), 2056)"
        with connection.cursor() as cur:
            # Cell size in metres so ~`cols` cells span the viewport's width.
            cur.execute(f"SELECT ST_XMax(g) - ST_XMin(g) FROM (SELECT {env} g) e", [west, south, east, north])
            width_m = cur.fetchone()[0] or 0.0
            size = max(width_m / cols, 1.0)

            where = ["b.geom IS NOT NULL", f"b.geom && {env}"]
            params = [size, size, west, south, east, north]
            for clause, val in self._filter_clauses(filters):
                where.append(clause)
                params.append(val)
            sql = (
                "SELECT ST_Y(ST_Transform(c, 4326)) AS lat, ST_X(ST_Transform(c, 4326)) AS lng, n FROM ("
                "SELECT ST_SnapToGrid(b.geom, %s, %s) AS c, count(*) AS n "
                "FROM building b WHERE " + " AND ".join(where) + " GROUP BY c) s"
            )
            cur.execute(sql, params)
            cells = [[row[0], row[1], row[2]] for row in cur.fetchall()]
        return {"cells": cells, "max": max((c[2] for c in cells), default=0)}
