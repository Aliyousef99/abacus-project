from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lineage', '0006_agent_deleted_at'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE lineage_agent DROP COLUMN IF EXISTS created_at;\n"
                "ALTER TABLE lineage_agent DROP COLUMN IF EXISTS updated_at;\n"
            ),
            reverse_sql=migrations.RunSQL.noop,
        )
    ]

