# Generated by Django 2.2.11 on 2020-09-08 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ET_Dashboard', '0004_notifications_campaign_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='grpc_id',
            field=models.IntegerField(default=1, max_length=256),
        ),
    ]
