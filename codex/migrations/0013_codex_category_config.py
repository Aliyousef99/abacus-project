from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codex', '0012_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodexCategoryConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('image_url', models.TextField(blank=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
    ]

