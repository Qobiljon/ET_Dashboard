# Generated by Django 2.2.11 on 2020-11-22 13:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ET_Dashboard', '0007_auto_20200909_0055'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='campaign',
            unique_together=None,
        ),
        migrations.DeleteModel(
            name='GrpcUserIds',
        ),
        migrations.DeleteModel(
            name='Notifications',
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='participant',
            name='campaign',
        ),
        migrations.DeleteModel(
            name='Campaign',
        ),
        migrations.DeleteModel(
            name='Participant',
        ),
    ]
