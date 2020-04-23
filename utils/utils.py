import time
import datetime

channel = None
stub = None
channel_is_open = False


def datetime_to_timestamp_ms(value: datetime):
    return int(round(value.timestamp() * 1000))


def timestamp_now_ms():
    return int(round(time.time() * 1000))


def timestamp_diff_in_days(a, b):
    return int((a - b) / 86400000)


def timestamp_to_readable_string(timestamp_ms):
    return datetime.datetime.fromtimestamp(float(timestamp_ms) / 1000).strftime('%Y/%m/%d %H:%M:%S')


def timestamp_to_web_string(timestamp_ms):
    date_time = datetime.datetime.fromtimestamp(float(timestamp_ms) / 1000)
    date_part = '-'.join([str(date_time.year), '%02d' % date_time.month, '%02d' % date_time.day])
    time_part = ':'.join(['%02d' % date_time.hour, '%02d' % date_time.minute])
    return 'T'.join([date_part, time_part])
