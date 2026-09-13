from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("gwr", "0001_initial")]
    operations = [
        migrations.AddIndex("entrance", GinIndex(fields=["search_vector"], name="entrance_sv_gin")),
        migrations.RunSQL(
            'CREATE INDEX entrance_strname_trgm ON entrance USING gin ("STRNAME" gin_trgm_ops);',
            "DROP INDEX IF EXISTS entrance_strname_trgm;",
        ),
    ]
