from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('codex', '0006_task_status_extend'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VaultItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(choices=[('SHELL_CORP', 'Shell Corporation'), ('BANK_ACCOUNT', 'Untraceable Bank Account'), ('CRYPTO_WALLET', 'Cryptocurrency Wallet'), ('KEYPASS', 'Key Passphrase')], max_length=20)),
                ('name', models.CharField(max_length=255)),
                ('identifier', models.CharField(blank=True, max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('secret', models.TextField(blank=True, help_text='Encrypted or protected secret payload')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
