#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/20/2024
# FoS for Intuitive Surgical
import os
import datetime
import re


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
UUID4_REGEX_PATTERN = r"[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}"


def collect_parameters(keys):
    """
    Ensure that we have all necessary environment variables based on a list of keys
    :param keys: A list of environment variable names
    """
    for key in keys:
        if key not in os.environ:
            raise SystemError(f'Missing environment variable: {key}')


def get_utcnow():
    """
    Get a string representing UTC now already preformatted with the desired output format
    :return: string
    """
    return datetime.datetime.now(datetime.timezone.utc).strftime(DATETIME_FORMAT)


def parse_iso8601(str_input):
    try:
        date, time = str_input.split('T', 1)
        if '-' in time:
            time, tz = time.split('-')
            tz = '-' + tz
        elif '+' in time:
            time, tz = time.split('+')
            tz = '+' + tz
        elif 'Z' in time:
            time = time[:-1]
            tz = '+0000'

        # For consistency, add microseconds if not present
        if '.' not in time:
            time += '.0'

        fmt = '%Y%m%dT%H%M%S.%f%z'
        return datetime.datetime.strptime(f"{date.replace('-', '')}T{time.replace(':', '')}{datetime.tz.replace(':', '')}", fmt)
    except (ValueError, NameError):
        raise ValueError(f'Unable to parse invalid ISO8601 datetime string {str_input}.')