from et_grpcs import et_service_pb2_grpc
import datetime
import time
import grpc


def get_stub_and_channel():
    channel = grpc.insecure_channel('127.0.0.1:50051')
    stub = et_service_pb2_grpc.ETServiceStub(channel)
    return stub, channel


def datetime_to_timestamp_ms(value: datetime):
    return int(round(value.timestamp() * 1000))


def timestamp_now_ms():
    return int(round(time.time() * 1000))


def calculate_day_number(join_timestamp):
    then = datetime.datetime.fromtimestamp(float(join_timestamp) / 1000).replace(hour=0, minute=0, second=0, microsecond=0)
    then += datetime.timedelta(days=1)

    now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    now += datetime.timedelta(days=1)

    return (now - then).days


def timestamp_to_readable_string(timestamp_ms):
    return datetime.datetime.fromtimestamp(float(timestamp_ms) / 1000).strftime('%m/%d %H:%M:%S')


def timestamp_to_web_string(timestamp_ms):
    date_time = datetime.datetime.fromtimestamp(float(timestamp_ms) / 1000)
    date_part = '-'.join([str(date_time.year), '%02d' % date_time.month, '%02d' % date_time.day])
    time_part = ':'.join(['%02d' % date_time.hour, '%02d' % date_time.minute])
    return 'T'.join([date_part, time_part])
