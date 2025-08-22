# Generated migration for stream_id to stream_key rename

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_processing', '0002_make_provider_nullable'),
    ]

    operations = [
        migrations.RenameField(
            model_name='videoanalysis',
            old_name='stream_id',
            new_name='stream_key',
        ),
        migrations.RenameField(
            model_name='processingqueue',
            old_name='stream_id',
            new_name='stream_key',
        ),
    ]