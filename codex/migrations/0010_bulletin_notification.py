from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('codex', '0009_propertydossier_vehicle'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bulletin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('audience', models.CharField(choices=[('HEIR', 'Heir'), ('OVERLOOKER', 'Overlooker'), ('ALL', 'All')], default='ALL', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bulletins_posted', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notif_type', models.CharField(choices=[('SILO_REPORT', 'New Silo Report'), ('TASK_ASSIGNED', 'Task Assigned'), ('OPERATION_STATUS', 'Operation Status Changed'), ('MANTLE', "Protector's Mantle")], max_length=40)),
                ('message', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BulletinAck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acknowledged_at', models.DateTimeField(auto_now_add=True)),
                ('bulletin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acks', to='codex.bulletin')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bulletin_acks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='bulletinack',
            unique_together={('bulletin', 'user')},
        ),
    ]

