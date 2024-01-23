#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/20/2024
# FoS for Intuitive Surgical
import os
import datetime


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
UUID4_REGEX_PATTERN = r"^[0-9(a-f|A-F)]{8}-[0-9(a-f|A-F)]{4}-4[0-9(a-f|A-F)]{3}-[89ab][0-9(a-f|A-F)]{3}-[0-9(a-f|A-F)]{12}$"


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


def get_patient_images(s3_client, patient_id: str):
    """
    Helper function to obtain all the medical images associated with the provided patient id
    :param s3_client: the boto3 s3_client handle
    :param str patient_id: uuid of the patient
    :return: list of patient image uris
    :rtype: list(dict)
    """
    paginator = s3_client.get_paginator('list_objects_v2')
    s3_objects = (
        s3_obj
        for page in paginator.paginate(Bucket=os.environ['PATIENT_IMG_BUCKET'], Prefix=patient_id)
        for s3_obj in page.get('Contents', [])
    )
    sorted_s3_objects = sorted(s3_objects, key=lambda obj: int(obj['LastModified'].strftime('%s')), reverse=True)
    return [format_patient_image_object(s3_object) for s3_object in sorted_s3_objects]


def format_patient_image_object(s3_object) -> dict:
    # incase there is a ".jpeg" extension remove it
    split_parts = s3_object['Key'].split("/")[1].split("Z")
    img_ts = f"{split_parts[0]}Z"
    return {
        'img_uri': f"{os.environ['PATIENT_IMG_BUCKET']}/{s3_object['Key']}",
        'img_timestamp': datetime.datetime.fromisoformat(img_ts)
    }