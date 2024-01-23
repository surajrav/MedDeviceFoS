#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/20/2024
# FoS for Intuitive Surgical
import os
import uuid
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
    # incase there is a ".jpeg" (or other img) extension remove it
    if "Z" in s3_object['Key']:
        split_parts = s3_object['Key'].split("/")[1].split("Z")
        img_ts = f"{split_parts[0]}Z"
    elif "." in s3_object['Key']:
        split_parts = s3_object['Key'].split("/")[1].rsplit(".", 1)
        img_ts = split_parts[0]

    return {
        'img_uri': f"{os.environ['PATIENT_IMG_BUCKET']}/{s3_object['Key']}",
        'img_timestamp': datetime.datetime.fromisoformat(img_ts)
    }


async def get_patient_entity(db_client, s3_client, patient_id):
    """
    Utility function to retrieve patient database entry provided `patient_id` specified exists in the
    database else returns None.

    This function also uses the provided `patient_id` to populate the returned patient entity with the
    patient's medical images if they're available.

    :param db_client:
    :param s3_client:
    :param patient_id:
    :return:
    """
    if (patient := await db_client.patients.find_one({"_id": uuid.UUID(patient_id)})) is not None:
        patient["images"] = get_patient_images(s3_client, patient_id)
        patient["date_of_birth"] = patient["date_of_birth"].date()
        return patient
    return None
