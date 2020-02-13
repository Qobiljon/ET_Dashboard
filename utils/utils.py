import datetime


def datetime_to_timestamp_ms(value: datetime):
    return int(round(value.timestamp() * 1000))
