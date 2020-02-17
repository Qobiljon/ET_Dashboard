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
