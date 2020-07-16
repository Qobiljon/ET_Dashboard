#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import signal
import grpc
from utils import utils
from et_grpcs import et_service_pb2_grpc


def handler(signal_received, frame):
    if utils.channel_is_open:
        utils.channel.close()
        utils.channel_is_open = False
        print('gRPC stopped')
        exit(0)


def setup_grpc():
    if not utils.channel_is_open:
        utils.channel = grpc.insecure_channel('127.0.0.1:50051')
        utils.stub = et_service_pb2_grpc.ETServiceStub(utils.channel)
        utils.channel_is_open = True
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
        print('gRPC channel opened')


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ET_Dashboard.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    setup_grpc()
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
