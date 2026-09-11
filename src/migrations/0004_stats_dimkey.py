from django.db import migrations

# Task 4: drop the baked-German dim_label column. Labels are now resolved per active
# language in Python (StatsService + LabelService), so mv_stats only needs the raw
# dimension key (canton abbrev / GKAT / GSTAT / GENH1 code / decade-start / WAZIM).
# No join to `code` is needed anymore.
CREATE_MV_STATS_NO_LABEL = """
DROP MATERIALIZED VIEW IF EXISTS mv_stats;
CREATE MATERIALIZED VIEW mv_stats AS
SELECT 'buildings_by_canton' metric, coalesce("GDEKT",'') dim_key, count(*)::float8 value
FROM building GROUP BY "GDEKT"
UNION ALL
SELECT 'buildings_by_category', coalesce("GKAT"::text,''), count(*)::float8
FROM building GROUP BY "GKAT"
UNION ALL
SELECT 'building_status', coalesce("GSTAT"::text,''), count(*)::float8
FROM building GROUP BY "GSTAT"
UNION ALL
SELECT 'heating_energy', coalesce("GENH1"::text,''), count(*)::float8
FROM building GROUP BY "GENH1"
UNION ALL
SELECT 'buildings_by_decade', coalesce(((("GBAUJ"/10)*10)::text),''), count(*)::float8
FROM building GROUP BY ("GBAUJ"/10)*10
UNION ALL
SELECT 'dwellings_by_rooms', coalesce("WAZIM"::text,''), count(*)::float8
FROM dwelling GROUP BY "WAZIM";
CREATE INDEX mv_stats_metric ON mv_stats (metric);
"""

# Reverse: restore the 0003 shape (metric, dim_key, dim_label, value) with baked German
# labels, so `migrate 0004 backwards` leaves the schema as 0003 left it.
RESTORE_MV_STATS_WITH_LABEL = """
DROP MATERIALIZED VIEW IF EXISTS mv_stats;
CREATE MATERIALIZED VIEW mv_stats AS
SELECT 'buildings_by_canton' metric, coalesce("GDEKT",'?') dim_key,
       coalesce("GDEKT",'unbekannt') dim_label, count(*)::float8 value
FROM building GROUP BY "GDEKT"
UNION ALL
SELECT 'buildings_by_category', coalesce(b."GKAT"::text,'?'),
       coalesce(c."CODTXTLD",'unbekannt'), count(*)::float8
FROM building b LEFT JOIN code c ON c."CMERKM"='GKAT' AND c."CECODID"=b."GKAT"
GROUP BY b."GKAT", c."CODTXTLD"
UNION ALL
SELECT 'building_status', coalesce(b."GSTAT"::text,'?'),
       coalesce(c."CODTXTLD",'unbekannt'), count(*)::float8
FROM building b LEFT JOIN code c ON c."CMERKM"='GSTAT' AND c."CECODID"=b."GSTAT"
GROUP BY b."GSTAT", c."CODTXTLD"
UNION ALL
SELECT 'heating_energy', coalesce(b."GENH1"::text,'?'),
       coalesce(c."CODTXTLD",'unbekannt'), count(*)::float8
FROM building b LEFT JOIN code c ON c."CMERKM"='GENH1' AND c."CECODID"=b."GENH1"
GROUP BY b."GENH1", c."CODTXTLD"
UNION ALL
SELECT 'buildings_by_decade',
       coalesce(((("GBAUJ"/10)*10)::text),'?'),
       coalesce(((("GBAUJ"/10)*10)::text || 'er'),'unbekannt'), count(*)::float8
FROM building GROUP BY ("GBAUJ"/10)*10
UNION ALL
SELECT 'dwellings_by_rooms', coalesce("WAZIM"::text,'?'),
       coalesce("WAZIM"::text || ' Zimmer','unbekannt'), count(*)::float8
FROM dwelling GROUP BY "WAZIM";
CREATE INDEX mv_stats_metric ON mv_stats (metric);
"""


class Migration(migrations.Migration):
    dependencies = [("src", "0003_stats_matview")]
    operations = [
        migrations.RunSQL(CREATE_MV_STATS_NO_LABEL, RESTORE_MV_STATS_WITH_LABEL),
    ]
