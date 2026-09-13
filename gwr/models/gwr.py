from django.contrib.gis.db import models as gis
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models


class Building(models.Model):
    EGID = models.IntegerField(primary_key=True, db_column="EGID")
    GDEKT = models.TextField(db_column="GDEKT", null=True, db_index=True)
    GGDENR = models.IntegerField(db_column="GGDENR", null=True)
    GGDENAME = models.TextField(db_column="GGDENAME", null=True)
    GKODE = models.FloatField(db_column="GKODE", null=True)
    GKODN = models.FloatField(db_column="GKODN", null=True)
    GSTAT = models.IntegerField(db_column="GSTAT", null=True)
    GKAT = models.IntegerField(db_column="GKAT", null=True, db_index=True)
    GKLAS = models.IntegerField(db_column="GKLAS", null=True)
    GBAUJ = models.IntegerField(db_column="GBAUJ", null=True, db_index=True)
    GBAUP = models.IntegerField(db_column="GBAUP", null=True)
    GAREA = models.IntegerField(db_column="GAREA", null=True)
    GEBF = models.IntegerField(db_column="GEBF", null=True)  # Energiebezugsfläche (heated surface m²)
    GVOL = models.IntegerField(db_column="GVOL", null=True)
    GASTW = models.IntegerField(db_column="GASTW", null=True)
    GANZWHG = models.IntegerField(db_column="GANZWHG", null=True)
    GENH1 = models.IntegerField(db_column="GENH1", null=True, db_index=True)
    GENH2 = models.IntegerField(db_column="GENH2", null=True)
    geom = gis.PointField(srid=2056, null=True, spatial_index=True)

    class Meta:
        db_table = "building"


class Entrance(models.Model):
    EGID = models.IntegerField(db_column="EGID", db_index=True)
    EDID = models.IntegerField(db_column="EDID", null=True)
    STRNAME = models.TextField(db_column="STRNAME", null=True)
    STRSP = models.IntegerField(db_column="STRSP", null=True)
    STROFFIZIEL = models.IntegerField(db_column="STROFFIZIEL", null=True)
    DEINR = models.TextField(db_column="DEINR", null=True)
    DPLZ4 = models.IntegerField(db_column="DPLZ4", null=True)
    DPLZNAME = models.TextField(db_column="DPLZNAME", null=True)
    DKODE = models.FloatField(db_column="DKODE", null=True)
    DKODN = models.FloatField(db_column="DKODN", null=True)
    address_label = models.TextField(null=True)
    search_vector = SearchVectorField(null=True)
    geom = gis.PointField(srid=2056, null=True)

    class Meta:
        db_table = "entrance"
        # Actual index creation lives in the hand-written 0002_search_indexes
        # migration (GinIndex here plus a raw-SQL gin_trgm_ops index on STRNAME);
        # declaring it in Meta too keeps makemigrations --check from reporting
        # drift between model state and the migration graph.
        indexes = [GinIndex(fields=["search_vector"], name="entrance_sv_gin")]


class Dwelling(models.Model):
    EGID = models.IntegerField(db_column="EGID", db_index=True)
    EWID = models.IntegerField(db_column="EWID", null=True)
    EDID = models.IntegerField(db_column="EDID", null=True)
    WSTWK = models.IntegerField(db_column="WSTWK", null=True)
    WBEZ = models.TextField(db_column="WBEZ", null=True)
    WSTAT = models.IntegerField(db_column="WSTAT", null=True)
    WAREA = models.IntegerField(db_column="WAREA", null=True)
    WAZIM = models.IntegerField(db_column="WAZIM", null=True)
    WKCHE = models.IntegerField(db_column="WKCHE", null=True)
    WBAUJ = models.IntegerField(db_column="WBAUJ", null=True)

    class Meta:
        db_table = "dwelling"


class Code(models.Model):
    CECODID = models.IntegerField(db_column="CECODID")
    CMERKM = models.TextField(db_column="CMERKM")
    CODTXTLD = models.TextField(db_column="CODTXTLD", null=True)  # German long
    CODTXTLF = models.TextField(db_column="CODTXTLF", null=True)  # French long
    CODTXTLI = models.TextField(db_column="CODTXTLI", null=True)  # Italian long

    class Meta:
        db_table = "code"
        indexes = [models.Index(fields=["CMERKM", "CECODID"])]
