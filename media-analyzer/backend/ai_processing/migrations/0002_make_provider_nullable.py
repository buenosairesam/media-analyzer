# Generated migration to make provider field nullable

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_processing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoanalysis',
            name='provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ai_processing.analysisprovider'),
        ),
    ]