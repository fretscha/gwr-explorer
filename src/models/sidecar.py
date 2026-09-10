from typing import ClassVar

from django.db import models


class MapPoint(models.Model):
    egid = models.IntegerField(db_index=True)
    lat = models.FloatField()
    lon = models.FloatField()
    canton = models.CharField(max_length=2, db_index=True, null=True)
    gkat = models.IntegerField(null=True, db_index=True)
    gbauj = models.IntegerField(null=True, db_index=True)
    genh1 = models.IntegerField(null=True, db_index=True)

    class Meta:
        app_label = "src"
        # Composite index for the map's viewport bbox query
        # (lat range-scanned, lon narrowed) — without it, MapService.points_in_bbox
        # full-scans all ~3.3M rows on every map pan/zoom at real scale.
        indexes: ClassVar = [models.Index(fields=["lat", "lon"])]


class StatsCache(models.Model):
    metric = models.CharField(max_length=64, db_index=True)
    dim_key = models.CharField(max_length=128)
    dim_label = models.CharField(max_length=255)
    value = models.FloatField()

    class Meta:
        app_label = "src"
        indexes: ClassVar = [models.Index(fields=["metric"])]
