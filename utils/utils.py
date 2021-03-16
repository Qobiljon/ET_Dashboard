from et_grpcs import et_service_pb2_grpc
from utils import settings
import datetime
import time
import grpc
import os
import re


def get_grpc_channel_stub():
    MAX_MESSAGE_LENGTH = 2147483647

    channel = grpc.insecure_channel('127.0.0.1:50051', options=[
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
    ])
    stub = et_service_pb2_grpc.ETServiceStub(channel=channel)
    return channel, stub


def datetime_to_timestamp_ms(value: datetime):
    return int(round(value.timestamp() * 1000))


def get_timestamp_hour(timestamp_ms):
    return datetime.datetime.fromtimestamp(timestamp_ms / 1000).hour


def timestamp_now_ms():
    return int(round(time.time() * 1000))


def calculate_day_number(join_timestamp):
    then = datetime.datetime.fromtimestamp(float(join_timestamp) / 1000).replace(hour=0, minute=0, second=0, microsecond=0)
    then += datetime.timedelta(days=1)

    now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    now += datetime.timedelta(days=1)

    return (now - then).days


def timestamp_to_readable_string(timestamp_ms):
    if timestamp_ms == 0:
        return "N/A"
    else:
        return datetime.datetime.fromtimestamp(float(timestamp_ms) / 1000).strftime('%m/%d (%a), %I:%M %p')


def timestamp_to_web_string(timestamp_ms):
    date_time = datetime.datetime.fromtimestamp(float(timestamp_ms) / 1000)
    date_part = '-'.join([str(date_time.year), '%02d' % date_time.month, '%02d' % date_time.day])
    time_part = ':'.join(['%02d' % date_time.hour, '%02d' % date_time.minute])
    return 'T'.join([date_part, time_part])


def get_download_file_path(file_name):
    if not os.path.exists(settings.download_dir):
        os.mkdir(settings.download_dir)
        os.chmod(settings.download_dir, 0o777)

    file_path = os.path.join(settings.download_dir, file_name)
    fp = open(file_path, 'w+')
    fp.close()

    os.chmod(file_path, 0o777)

    return file_path


def is_numeric(string, floating=False):
    if floating:
        return re.search(pattern=r'^[+-]?\d+\.\d+$', string=string) is not None
    else:
        return re.search(pattern=r'^[+-]?\d+$', string=string) is not None


def param_check(request_body, params):
    for param in params:
        if param not in request_body:
            return False
    return True
