from django.contrib.auth.models import User
from django.db import models


class GrpcUserIds(models.Model):
    email = models.CharField(max_length=256, unique=True)
    user_id = models.IntegerField()

    @staticmethod
    def get_id(email):
        if GrpcUserIds.objects.filter(email=email).exists():
            return GrpcUserIds.objects.get(email=email).user_id
        else:
            return None

    @staticmethod
    def create_or_update(email, user_id):
        if GrpcUserIds.objects.filter(email=email).exists():
            row = GrpcUserIds.objects.get(email=email)
            row.user_id = user_id
            row.save()
        else:
            GrpcUserIds.objects.create(email=email, user_id=user_id)


class PresetDataSources:
    android_sensors = [
        {'name': 'ANDROID_ACCELEROMETER', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_ACCELEROMETER_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_GAME_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_AMBIENT_TEMPERATURE', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_GEOMAGNETIC_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_GRAVITY', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_GYROSCOPE', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_GYROSCOPE_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_HEART BEAT', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_HEART RATE', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_LIGHT', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_LINEAR_ACCELERATION', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_LOW_LATENCY_OFFBODY_DETECT', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_MAGNETIC_FIELD', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_MAGNETIC_FIELD_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_MOTION_DETECTION', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_ORIENTATION', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_POSE_6DOF', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_PRESSURE', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_PROXIMITY', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_RELATIVE_HUMIDITY', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_SIGNIFICANT_MOTION', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_STATIONARY_DETECT', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_STEP_COUNTER', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_STEP_DETECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_TEMPERATURE', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
        {'name': 'ANDROID_GPS', 'icon': 'smartphone-android-data-source.png', 'type': 'rate'},
    ]
    tizen_sensors = [
        {'name': 'TIZEN_ACCELEROMETER', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_GRAVITY', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_GYROSCOPE', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_HRM', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_HUMIDITY', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_LIGHT', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_LINEARACCELERATION', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_MAGNETOMETER', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_ORIENTATION', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_PRESSURE', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_PROXIMITY', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_TEMPERATURE', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_ULTRAVIOLET', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
        {'name': 'TIZEN_GPS', 'icon': 'wearable-tizen-data-source.png', 'type': 'rate'},
    ]
    others = [
        {'name': 'SURVEY_EMA', 'icon': 'survey-data-source.png', 'type': 'json'},
        {'name': 'APPLICATION_USAGE', 'icon': 'app-usage-data-source.png', 'type': 'json'},
        {'name': 'VOICE_RECORDING', 'icon': 'voice-recording-data-source.png', 'type': 'json'},
    ]

    @staticmethod
    def all_preset_data_sources():
        return PresetDataSources.others + PresetDataSources.android_sensors + PresetDataSources.tizen_sensors


class Campaign(models.Model):
    campaign_id = models.IntegerField()
    requester_email = models.CharField(max_length=128)
    name = models.CharField(max_length=256)
    notes = models.TextField()
    start_timestamp = models.BigIntegerField()
    end_timestamp = models.BigIntegerField()
    creator_email = models.CharField(max_length=128)
    config_json = models.TextField()
    participant_count = models.IntegerField()

    class Meta:
        unique_together = ['campaign_id', 'requester_email']

    @classmethod
    def create_or_update(cls, campaign_id, requester_email, name, notes, start_timestamp, end_timestamp, creator_email, config_json, participant_count):
        if Campaign.objects.filter(campaign_id=campaign_id, requester_email=requester_email).exists():
            campaign = Campaign.objects.get(campaign_id=campaign_id, requester_email=requester_email)
            campaign.requester_email = requester_email
            campaign.name = name
            campaign.notes = notes
            campaign.start_timestamp = start_timestamp
            campaign.end_timestamp = end_timestamp
            campaign.creator_email = creator_email
            campaign.config_json = config_json
            campaign.participant_count = participant_count
            campaign.save()
        else:
            Campaign.objects.create(
                campaign_id=campaign_id,
                requester_email=requester_email,
                name=name, notes=notes,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                creator_email=creator_email,
                config_json=config_json,
                participant_count=participant_count
            )
