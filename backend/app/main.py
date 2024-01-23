#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/20/2024
# FoS for Intuitive Surgical
import os
import datetime
import boto3
from botocore.exceptions import ClientError
from typing import Annotated
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from pymongo.server_api import ServerApi
from fastapi import FastAPI, Path, File, Form, UploadFile, HTTPException
from . import utils, models


# before we initiate the FastAPI app ensure that we have all the required environment (mongodb info, minio, etc)
# and if not then this util function should raise a system error (fail with required info early)
utils.collect_parameters([
    "MINIO_SERVER_HOST", "MINIO_SERVER_ACCESS_KEY", "MINIO_SERVER_SECRET_KEY",
    "DB_NAME", "DB_HOST", "DB_USER", "DB_PASS",
    "PATIENT_IMG_BUCKET"
])

# Establish the FastAPI app
app = FastAPI()


@app.on_event("startup")
async def startup_db_client():
    """
    Establish the mongodb connection on FastAPI app startup
    """
    mongo_uri = f"mongodb://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:27017/{os.environ['DB_NAME']}"
    app.mongodb_client = AsyncIOMotorClient(mongo_uri, server_api=ServerApi('1'))
    app.mongodb = app.mongodb_client[os.environ['DB_NAME']]
    app.s3_boto = boto3.client('s3',
        endpoint_url=f"http://{os.environ["MINIO_SERVER_HOST"]}:9000",
        aws_access_key_id=os.environ["MINIO_SERVER_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SERVER_SECRET_KEY"]
    )


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


async def ping_server():
    # Send a ping to confirm a successful connection
    try:
        await app.mongodb_client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)


@app.post(
    "/patients/",
    response_description="Create a new patient record",
    response_model=models.Patient,
    status_code=201,  # for created
    response_model_by_alias=False
)
async def create_patient(patient: models.Patient):
    """
    Insert a new patient record.

    A unique `id` will be created and provided in the response.

    Note: THe patient's medical image will have to uploaded post this create operation, using
    this returned `id` over at the update endpoint (PUT)
    """
    # TODO: Optimize to one call instead of insert_one and find_one
    new_patient = await models.Patient.insert_one(models.Patient.model_dump(by_alias=True, exclude=["id"]))
    created_patient = await app.mongodb.patients.find_one({"_id": new_patient.inserted_id})
    return created_patient


@app.get(
    "/patients/{patient_id}",
    response_model=models.Patient,
    response_model_by_alias=False
)
async def get_patient(
        patient_id: Annotated[str, Path(pattern=utils.UUID4_REGEX_PATTERN, description="The ID of the patient whose data to get")]
):
    await ping_server()
    # Note: First time using the walrus operator for me (Syntactic Sugar FTW!)
    if (patient := await app.mongodb.patients.find_one({"_id": patient_id})) is not None:
        return patient

    raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")


@app.get(
    "/patients/",
    response_description="List all patients",
    response_model=models.PatientCollection,
    response_model_by_alias=False
)
async def list_patients():
    """
    List all patients.

    TODO: This is currently non-paginated and limited to the first 1000 records, fix with pagination
    """
    await ping_server()
    return models.PatientCollection(patients=await app.mongodb.patients.find().to_list(length=1000))


@app.put(
    "/patients/{patient_id}",
    response_model=models.Patient,
    response_model_by_alias=False,
    response_description="Add/Update the specified patient's medical image"
)
async def update_patient(
        patient_id: Annotated[str, Path(pattern=utils.UUID4_REGEX_PATTERN, description="The ID of the patient for which the medical image is being uploaded")],
        uploaded_img_file: Annotated[UploadFile, File(description="Patient Medical Image")],
        img_timestamp: Annotated[str | None, Form(description="Patient Medical Image Timestamp specified in ISO8601 DateTime format")]
):
    """
    Add/Update the patient's medical image

    Note if an image is specified and a previous one already exists then this will override the existing image.

    If a timestamp is not specified via the `img_timestamp` form string attribute in the ISO 8601 format, then the current
    utc time will be stored.
    """
    try:
        img_ts = datetime.datetime.now(datetime.timezone.utc) if img_timestamp is None else utils.parse_iso8601(img_timestamp)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=[{
                'loc': ["form", 'img_timestamp'],
                'msg': f"img_timestamp '{img_timestamp}' is not per ISO8601 datetime spec",
                'type': 'value_error.str.format'
            }]
        )

    try:
        uploaded_img_file.seek(0)
        response = app.s3_boto.upload_fileobj(
            uploaded_img_file.file, os.environ["PATIENT_IMG_BUCKET"], f"{patient_id}/{uploaded_img_file.filename}"
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Object storage upload error: {e.response['Error']['Message']}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    finally:
        uploaded_img_file.file.close()

    updated_patient = await app.mongodb.patients.find_one_and_update(
        {"_id": patient_id},
        {"$set": {
            "img_timestamp": img_ts,
            "img_uri": f"{patient_id}/{uploaded_img_file.filename}"
        }},
        return_document=ReturnDocument.AFTER,
    )
    if updated_patient is not None:
        return updated_patient
    else:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
