from django.contrib.auth.models import User
from django.db import models
from django.core.validators import int_list_validator
from utils import utils


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
        {'name': 'ANDROID_ACCELEROMETER', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_ACCELEROMETER_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_GAME_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_AMBIENT_TEMPERATURE', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_GEOMAGNETIC_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_GRAVITY', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_GYROSCOPE', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_GYROSCOPE_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_HEART_BEAT', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_HEART_RATE', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_LIGHT', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_LINEAR_ACCELERATION', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_LOW_LATENCY_OFFBODY_DETECT', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_MAGNETIC_FIELD', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_MAGNETIC_FIELD_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_MOTION_DETECTION', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_ORIENTATION', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_POSE_6DOF', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_PRESSURE', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_PROXIMITY', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_RELATIVE_HUMIDITY', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_SIGNIFICANT_MOTION', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_STATIONARY_DETECT', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_STEP_COUNTER', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_STEP_DETECTOR', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_TEMPERATURE', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
        {'name': 'ANDROID_GPS', 'icon': 'smartphone-android-data-source.png', 'type': 'delay'},
    ]
    tizen_sensors = [
        {'name': 'TIZEN_ACCELEROMETER', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_GRAVITY', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_GYROSCOPE', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_HRM', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_HUMIDITY', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_LIGHT', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_LINEARACCELERATION', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_MAGNETOMETER', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_ORIENTATION', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_PRESSURE', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_PROXIMITY', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_TEMPERATURE', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_ULTRAVIOLET', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
        {'name': 'TIZEN_GPS', 'icon': 'wearable-tizen-data-source.png', 'type': 'delay'},
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


class Participant(models.Model):
    email = models.CharField(max_length=256)
    campaign = models.ForeignKey(to=Campaign, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=256)
    day_no = models.IntegerField(default=None)
    amount_of_data = models.IntegerField(default=None)
    last_heartbeat_time = models.CharField(max_length=64, default=None)
    last_sync_time = models.CharField(max_length=64, default=None)
    data_source_ids = models.CharField(validators=[int_list_validator], max_length=512)
    per_data_source_amount_of_data = models.CharField(validators=[int_list_validator], max_length=512)

    class Meta:
        unique_together = ['email', 'campaign_id']

    @staticmethod
    def create_or_update(email, campaign, full_name, day_no, amount_of_data, last_heartbeat_time, last_sync_time, data_source_ids, per_data_source_amount_of_data):
        if len(data_source_ids) != len(per_data_source_amount_of_data):
            print('data_source_ids', data_source_ids)
            print('per_data_source_amount_of_data', per_data_source_amount_of_data)
            raise ValueError('lengths of arrays for data source ids and their amounts of data do not match (%d != %d)' % (len(data_source_ids), len(per_data_source_amount_of_data)))
        elif Participant.objects.filter(email=email, campaign=campaign).exists():
            participant = Participant.objects.get(email=email, campaign=campaign)
            participant.full_name = full_name
            participant.day_no = day_no
            participant.amount_of_data = amount_of_data
            participant.last_heartbeat_time = last_heartbeat_time
            participant.last_sync_time = last_sync_time
            participant.data_source_ids = ','.join(str(elem) for elem in data_source_ids)
            participant.per_data_source_amount_of_data = ','.join(str(elem) for elem in per_data_source_amount_of_data)
            participant.save()
        else:
            Participant.objects.create(
                email=email,
                campaign=campaign,
                full_name=full_name,
                day_no=day_no,
                amount_of_data=amount_of_data,
                last_heartbeat_time=last_heartbeat_time,
                last_sync_time=last_sync_time,
                data_source_ids=','.join(str(elem) for elem in data_source_ids),
                per_data_source_amount_of_data=','.join(str(elem) for elem in per_data_source_amount_of_data)
            ).save()


class DataSource:
    def __init__(self, data_source_id, name, icon_name, amount_of_data, delay=None, json=None):
        self.data_source_id = data_source_id
        self.name = name
        self.icon_name = icon_name
        self.amount_of_data = amount_of_data
        if delay is None:
            self.json = json
        elif json is None:
            self.delay = delay
        else:
            raise ValueError('DataSource.__init__(): Bad data source, either delay or json must be passed!')


class Record:
    def __init__(self, timestamp_ms, value):
        self.time = utils.timestamp_to_readable_string(timestamp_ms=timestamp_ms)
        self.value = value
