from django.contrib.auth.models import User
from django.db import models
from django.core.validators import int_list_validator
from utils import utils
import json

# gRPC
from et_grpcs import et_service_pb2


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


class Campaign(models.Model):
    campaign_id = models.IntegerField()
    requester_email = models.CharField(max_length=128)
    name = models.CharField(max_length=256)
    notes = models.TextField()
    start_timestamp = models.BigIntegerField()
    end_timestamp = models.BigIntegerField()
    remove_inactive_users_timeout = models.IntegerField()
    creator_email = models.CharField(max_length=128)
    config_json = models.TextField()
    participant_count = models.IntegerField()

    class Meta:
        unique_together = ['campaign_id', 'requester_email']

    def start_timestamp_for_web(self):
        return utils.timestamp_to_web_string(timestamp_ms=self.start_timestamp)

    def end_timestamp_for_web(self):
        return utils.timestamp_to_web_string(timestamp_ms=self.end_timestamp)

    @classmethod
    def create_or_update(cls, campaign_id, requester_email, name, notes, start_timestamp, end_timestamp, remove_inactive_users_timeout, creator_email, config_json, participant_count):
        if Campaign.objects.filter(campaign_id=campaign_id, requester_email=requester_email).exists():
            campaign = Campaign.objects.get(campaign_id=campaign_id, requester_email=requester_email)
            campaign.requester_email = requester_email
            campaign.name = name
            campaign.notes = notes
            campaign.start_timestamp = start_timestamp
            campaign.end_timestamp = end_timestamp
            campaign.remove_inactive_users_timeout = remove_inactive_users_timeout
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
                remove_inactive_users_timeout=remove_inactive_users_timeout,
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
    per_data_source_amount_of_data = models.CharField(validators=[int_list_validator], max_length=1024)
    per_data_source_last_sync_time = models.CharField(max_length=2048)

    class Meta:
        unique_together = ['email', 'campaign']

    @staticmethod
    def create_or_update(email, campaign, full_name, day_no, amount_of_data, last_heartbeat_time, last_sync_time, data_source_ids, per_data_source_amount_of_data, per_data_source_last_sync_time):
        if len(data_source_ids) != len(per_data_source_amount_of_data) or len(data_source_ids) != len(per_data_source_last_sync_time):
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
            participant.per_data_source_last_sync_time = ','.join(per_data_source_last_sync_time)
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
                per_data_source_amount_of_data=','.join(str(elem) for elem in per_data_source_amount_of_data),
                per_data_source_last_sync_time=','.join(str(elem) for elem in per_data_source_last_sync_time)
            ).save()


class Notifications(models.Model):
    notification_id = models.IntegerField(unique=True)
    campaign_id = models.IntegerField()
    timestamp = models.BigIntegerField()
    subject = models.CharField(max_length=512)
    content = models.CharField(max_length=2048)
    read = models.BooleanField(default=False)


class DataSource:
    def __init__(self, data_source_id, name, icon_name, amount_of_data, last_sync_time, config_json):
        self.data_source_id = data_source_id
        self.name = name
        self.icon_name = icon_name
        self.amount_of_data = amount_of_data
        self.last_sync_time = last_sync_time
        self.config_json = config_json
        self.selected = False

    others = [
        {'name': 'SURVEY_EMA', 'icon': 'survey-data-source.png'},
        {'name': 'APPLICATION_USAGE', 'icon': 'app-usage-data-source.png'},
        {'name': 'AUDIO_LOUDNESS', 'icon': 'audio-loudness-data-source.png'},
        {'name': 'GEOFENCE', 'icon': 'geofence-data-source.png'},
        {'name': 'LOCATION_GPS', 'icon': 'location-data-source.png'},
        {'name': 'STATIONARY_DURATION', 'icon': 'stationary-duration-data-source.png'},
        {'name': 'SCREEN_ON_OFF', 'icon': 'screen-on-off-data-source.png'},
        {'name': 'UNLOCK_DURATION', 'icon': 'unlock-duration-data-source.png'},
        {'name': 'CALLS', 'icon': 'calls-data-source.png'},
        {'name': 'MESSAGES', 'icon': 'messages-data-source.png'},
        {'name': 'ACTIVITY_RECOGNITION', 'icon': 'activity-recognition-data-source.png'},
        {'name': 'ACTIVITY_TRANSITION', 'icon': 'activity-transition-data-source.png'},
    ]
    android_sensors = [
        {'name': 'ANDROID_ACCELEROMETER', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_ACCELEROMETER_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GAME_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_AMBIENT_TEMPERATURE', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GEOMAGNETIC_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GRAVITY', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GYROSCOPE', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GYROSCOPE_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_HEART_BEAT', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_HEART_RATE', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_LIGHT', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_LINEAR_ACCELERATION', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_LOW_LATENCY_OFFBODY_DETECT', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_MAGNETIC_FIELD', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_MAGNETIC_FIELD_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_MOTION_DETECTION', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_ORIENTATION', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_POSE_6DOF', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_PRESSURE', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_PROXIMITY', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_RELATIVE_HUMIDITY', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_SIGNIFICANT_MOTION', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_STATIONARY_DETECT', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_STEP_COUNTER', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_STEP_DETECTOR', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_TEMPERATURE', 'icon': 'smartphone-android-data-source.png'},
    ]
    tizen_sensors = [
        {'name': 'TIZEN_ACCELEROMETER', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_GRAVITY', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_GYROSCOPE', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_HRM', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_HUMIDITY', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_LIGHT', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_LINEARACCELERATION', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_MAGNETOMETER', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_ORIENTATION', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_PRESSURE', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_PROXIMITY', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_TEMPERATURE', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_ULTRAVIOLET', 'icon': 'wearable-tizen-data-source.png'},
        {'name': 'TIZEN_GPS', 'icon': 'wearable-tizen-data-source.png'},
    ]

    @staticmethod
    def all_data_sources_no_details(user_id, email, use_grpc=True, map_with_name=False):
        data_source_list = []
        data_source_dict = {}
        if use_grpc:
            grpc_req = et_service_pb2.RetrieveAllDataSourcesRequestMessage(userId=user_id, email=email)
            grpc_res = utils.stub.retrieveAllDataSources(grpc_req)
            if grpc_res.doneSuccessfully:
                for data_source_id, name, icon_name in zip(grpc_res.dataSourceId, grpc_res.name, grpc_res.iconName):
                    data_source = DataSource(
                        data_source_id=data_source_id,
                        name=name,
                        icon_name=icon_name,
                        amount_of_data=-1,
                        config_json=None,
                        last_sync_time=None
                    )
                    data_source_dict[name] = data_source
                    data_source_list += [data_source]
        for elem in DataSource.others + DataSource.android_sensors + DataSource.tizen_sensors:
            if elem['name'] not in data_source_dict:
                data_source = DataSource(
                    data_source_id=-1,
                    name=elem['name'],
                    icon_name=elem['icon'],
                    amount_of_data=-1,
                    config_json=None,
                    last_sync_time=None
                )
                data_source_dict[elem['name']] = data_source
                data_source_list += [data_source]
        if map_with_name:
            return data_source_dict
        else:
            data_source_list.sort(key=lambda key: key.name)
            return data_source_list

    @staticmethod
    def participants_data_sources_details(campaign: Campaign, trg_participant: Participant):
        data_sources = []
        amount_of_data_map = {}
        last_sync_time_map = {}
        for data_source_id, amount_of_data, last_sync_time in zip(trg_participant.data_source_ids.split(','), trg_participant.per_data_source_amount_of_data.split(','), trg_participant.per_data_source_last_sync_time.split(',')):
            amount_of_data_map[int(data_source_id)] = int(amount_of_data)
            last_sync_time_map[int(data_source_id)] = last_sync_time
        for config_json in json.loads(s=campaign.config_json):
            data_sources += [DataSource(
                data_source_id=config_json['data_source_id'],
                name=config_json['name'],
                icon_name=config_json['icon_name'],
                amount_of_data=amount_of_data_map[config_json['data_source_id']],
                last_sync_time=last_sync_time_map[config_json['data_source_id']],
                config_json=config_json['config_json']
            )]
        data_sources.sort(key=lambda key: key.name)
        return data_sources


class Record:
    def __init__(self, timestamp_ms, value):
        self.time = utils.timestamp_to_readable_string(timestamp_ms=timestamp_ms)
        self.value = value


class Echo(object):
    def write(self, value):
        return value
