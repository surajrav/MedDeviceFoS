#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/20/2024
# FoS for Intuitive Surgical
import os
import datetime
import uuid
import boto3
from contextlib import asynccontextmanager
from botocore.exceptions import ClientError
from typing import Annotated, Union
from motor.motor_asyncio import AsyncIOMotorClient
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Establish the mongodb connection on FastAPI app startup
    """
    # Operations to perform prior to whence the app starts taking requests

    # Motor (mongo's async python client) setup
    mongo_uri = f"mongodb://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:27017/{os.environ['DB_NAME']}"
    app.mongodb_client = AsyncIOMotorClient(mongo_uri, server_api=ServerApi('1'), uuidRepresentation="standard")
    app.mongodb = app.mongodb_client[os.environ['DB_NAME']]

    # object storage boto3 client setup
    app.s3_boto = boto3.client('s3',
        endpoint_url=f"http://{os.environ["MINIO_SERVER_HOST"]}:9000",
        aws_access_key_id=os.environ["MINIO_SERVER_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SERVER_SECRET_KEY"]
    )

    # This yields execution back to the FastAPI which starts taking requests
    yield

    # Any shutdown cleanup and resource clearance should go here
    app.mongodb_client.close()


# Establish the FastAPI app
app = FastAPI(lifespan=lifespan)


@app.post(
    "/patients/",
    response_description="Create a new patient record",
    response_model=models.Patient,
    status_code=201,  # for created
    response_model_by_alias=False
)
async def create_patient(patient: models.PatientInput):
    """
    Create a new patient record.

    A unique `id` will be created and provided in the response.

    Note: The patient's medical image(s) will have to uploaded post this create operation, using
    this returned `id` over at the update endpoint (PUT)
    """
    # TODO: Optimize to one call instead of insert_one and find_one
    patient_data = patient.model_dump(by_alias=True)
    patient_data["date_of_birth"] =  datetime.datetime.combine(patient_data["date_of_birth"], datetime.time.min)
    # see https://stackoverflow.com/a/44273588 for why I'm converting to datetime
    new_patient = await app.mongodb.patients.insert_one(patient_data)
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
    """
    Retrieve a patient's detailed medical record with images (if available) via the `patient_id` parameter specified.

    For the `img_uri` (if available in `images`), access the image at the current base url you're using to access this api
    plus this uri.

    For example, if using this api at localhost as follows: http://localhost/api/v1/patients/{patient_id}
    then use the value specified via the `img_uri` by suffixing to the above base url as follows:
    http://localhost/{img_uri}

    :param patient_id:
    :return:
    """
    # Note: First time using the walrus operator for me (Syntactic Sugar FTW!)
    if (patient := await utils.get_patient_entity(app.mongodb, app.s3_boto, patient_id)) is not None:
        return patient
    else:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")


@app.get(
    "/patients/",
    response_description="List all patients",
    response_model=models.PatientCollection,
    response_model_by_alias=False
)
async def list_patients():
    """
    This endpoint provides an abridged list of patient entities enough for the physician to search through
    and then retrieve a detailed entity via the GET (singular) patient data endpoint using the id obtained here.

    TODO: This is currently non-paginated and limited to the first 1000 records, fix with pagination
    """
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
        img_timestamp: Union[str, None] = Form(default=None, description="Patient Medical Image Timestamp specified in ISO8601 DateTime format")
):
    """
    Add a medical image to the patient's medical images set

    If a timestamp is not specified via the `img_timestamp` form string attribute in the ISO 8601 format, then the current
    utc time will be stored.
    """
    try:
        img_timestamp = img_timestamp or utils.get_utcnow()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=[{
                'loc': ["form", 'img_timestamp'],
                'msg': f"img_timestamp '{img_timestamp}' is not per ISO8601 datetime spec",
                'type': 'value_error.str.format'
            }]
        )

    if (patient := await app.mongodb.patients.find_one({"_id": uuid.UUID(patient_id)})) is not None:
        try:
            file_type_suffix = uploaded_img_file.filename.rsplit(".", 1)
            file_type_suffix = f".{file_type_suffix[1]}" if len(file_type_suffix) > 1 else ""
            await uploaded_img_file.seek(0)
            app.s3_boto.upload_fileobj(
                uploaded_img_file.file, os.environ["PATIENT_IMG_BUCKET"], f"{patient_id}/{img_timestamp}{file_type_suffix}"
            )
            patient["images"] = utils.get_patient_images(app.s3_boto, patient_id)
            patient["date_of_birth"] = patient["date_of_birth"].date()
            return patient
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Object storage upload error: {e.response['Error']['Message']}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
        finally:
            uploaded_img_file.file.close()
    else:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
