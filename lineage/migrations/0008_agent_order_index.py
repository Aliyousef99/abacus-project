from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lineage', '0007_drop_legacy_created_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='agent',
            name='order_index',
            field=models.IntegerField(blank=True, null=True, help_text='Manual ordering; lower appears first.'),
        ),
    ]

