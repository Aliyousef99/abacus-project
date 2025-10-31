from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codex', '0009_propertydossier_vehicle'),
    ]

    operations = [
        migrations.AddField(
            model_name='codexentry',
            name='summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='codexentry',
            name='image_urls',
            field=models.TextField(blank=True, help_text='Comma-separated image URLs for gallery'),
        ),
    ]

