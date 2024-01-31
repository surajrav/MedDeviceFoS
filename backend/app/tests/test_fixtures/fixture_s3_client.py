#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/30/2024
# FoS for Intuitive Surgical
import os
import boto3
import pytest_asyncio


@pytest_asyncio.fixture(scope="function", autouse=True)
async def s3_client():

    # Test setup
    # hijack os env for s3 bucket and replace with test s3 bucket
    orig_s3_bucket_name = os.environ.get("PATIENT_IMG_BUCKET")
    os.environ["PATIENT_IMG_BUCKET"] = os.environ.get("TEST_PATIENT_IMG_BUCKET")

    s3_client = boto3.client('s3',
        endpoint_url=f"http://{os.environ["MINIO_SERVER_HOST"]}:9000",
        aws_access_key_id=os.environ["MINIO_SERVER_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SERVER_SECRET_KEY"]
    )
    s3_resource = boto3.resource('s3',
        endpoint_url=f"http://{os.environ["MINIO_SERVER_HOST"]}:9000",
        aws_access_key_id=os.environ["MINIO_SERVER_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SERVER_SECRET_KEY"]
    )
    test_bucket_resource = s3_resource.Bucket(os.environ["TEST_PATIENT_IMG_BUCKET"])
    test_bucket_resource.objects.all().delete()

    # Yield and perform tests
    yield s3_client, test_bucket_resource

    # for teardown restore the env var for the s3 bucket
    test_bucket_resource.objects.all().delete()
    os.environ["PATIENT_IMG_BUCKET"] = orig_s3_bucket_name
