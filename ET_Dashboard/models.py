from django.contrib.auth.models import User
from django.db import models


class Campaigns(models.Model):
    id = models.AutoField(primary_key=True)
    creatorEmail = models.EmailField(null=False)
    title = models.CharField(max_length=256)
    notes = models.TextField(default='', null=False)
    participants = models.TextField(default='', null=False)


class UserToGrpcIdMap(models.Model):
    user = models.OneToOneField(to=User, primary_key=True, on_delete=models.CASCADE)
    gRPCId = models.IntegerField(null=False)


class DataSourceByCampaigns(models.Model):
    campaign = models.ForeignKey(to=Campaigns, on_delete=models.CASCADE)
    dataSourceName = models.CharField(max_length=256, null=False)


class PresetDataSources:
    android_sensors = [
        {'name': 'ANDROID_ACCELEROMETER', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_ACCELEROMETER_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GAME_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_AMBIENT_TEMPERATURE', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GEOMAGNETIC_ROTATION_VECTOR', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GRAVITY', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GYROSCOPE', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_GYROSCOPE_UNCALIBRATED', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_HEART BEAT', 'icon': 'smartphone-android-data-source.png'},
        {'name': 'ANDROID_HEART RATE', 'icon': 'smartphone-android-data-source.png'},
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
        {'name': 'ANDROID_GPS', 'icon': 'smartphone-android-data-source.png'},
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
    others = [
        {'name': 'SURVEY_EMA', 'icon': 'survey-data-source.png'},
        {'name': 'APPLICATION_USAGE', 'icon': 'app-usage-data-source.png'},
        {'name': 'VOICE_RECORDING', 'icon': 'voice-recording-data-source.png'},
    ]
