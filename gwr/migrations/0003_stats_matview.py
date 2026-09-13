from django.db import migrations

CREATE_MV_STATS = """
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

DROP_MV_STATS = "DROP MATERIALIZED VIEW IF EXISTS mv_stats;"


class Migration(migrations.Migration):
    dependencies = [("gwr", "0002_search_indexes")]
    operations = [
        migrations.RunSQL(CREATE_MV_STATS, DROP_MV_STATS),
    ]
