from django.db import models


class Building(models.Model):
    EGID = models.IntegerField(primary_key=True, db_column="EGID")
    GDEKT = models.TextField(db_column="GDEKT", null=True)
    GGDENR = models.IntegerField(db_column="GGDENR", null=True)
    GGDENAME = models.TextField(db_column="GGDENAME", null=True)
    GKODE = models.FloatField(db_column="GKODE", null=True)
    GKODN = models.FloatField(db_column="GKODN", null=True)
    GSTAT = models.IntegerField(db_column="GSTAT", null=True)
    GKAT = models.IntegerField(db_column="GKAT", null=True)
    GKLAS = models.IntegerField(db_column="GKLAS", null=True)
    GBAUJ = models.IntegerField(db_column="GBAUJ", null=True)
    GBAUP = models.IntegerField(db_column="GBAUP", null=True)
    GAREA = models.IntegerField(db_column="GAREA", null=True)
    GVOL = models.IntegerField(db_column="GVOL", null=True)
    GASTW = models.IntegerField(db_column="GASTW", null=True)
    GANZWHG = models.IntegerField(db_column="GANZWHG", null=True)
    GENH1 = models.IntegerField(db_column="GENH1", null=True)
    GENH2 = models.IntegerField(db_column="GENH2", null=True)

    class Meta:
        managed = False
        db_table = "building"
        app_label = "src"


class Entrance(models.Model):
    # These SQLite tables have no `id` column and a composite declared PRIMARY KEY,
    # so they are not rowid-alias tables. Django still requires a single-column pk,
    # so we expose SQLite's implicit `rowid` as the pk instead of a synthetic AutoField
    # (an AutoField would not correspond to any real column and reads would fail with
    # "no such column: id").
    id = models.IntegerField(primary_key=True, db_column="rowid")
    EGID = models.IntegerField(db_column="EGID")
    EDID = models.IntegerField(db_column="EDID", null=True)
    DEINR = models.TextField(db_column="DEINR", null=True)
    STRNAME = models.TextField(db_column="STRNAME", null=True)
    DPLZ4 = models.IntegerField(db_column="DPLZ4", null=True)
    DPLZNAME = models.TextField(db_column="DPLZNAME", null=True)
    DKODE = models.FloatField(db_column="DKODE", null=True)
    DKODN = models.FloatField(db_column="DKODN", null=True)

    class Meta:
        managed = False
        db_table = "entrance"
        app_label = "src"


class Dwelling(models.Model):
    id = models.IntegerField(primary_key=True, db_column="rowid")
    EGID = models.IntegerField(db_column="EGID")
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
        managed = False
        db_table = "dwelling"
        app_label = "src"


class Code(models.Model):
    id = models.IntegerField(primary_key=True, db_column="rowid")
    CECODID = models.IntegerField(db_column="CECODID")
    CMERKM = models.TextField(db_column="CMERKM")
    CODTXTLD = models.TextField(db_column="CODTXTLD", null=True)

    class Meta:
        managed = False
        db_table = "code"
        app_label = "src"
