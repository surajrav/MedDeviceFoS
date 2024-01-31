#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/22/2024
import os
import pathlib
import datetime
from . import models


FIXTURE_DATA = [
    {
        "first_name": "Jim",
        "last_name": "Jones",
        "date_of_birth": "1960-10-01",
        "images_lst": [
            {
                "img_uri": "img_dataset/1.jpg",
                "img_timestamp": "2021-02-01T00:00:00"
            },
            {
                "img_uri": "img_dataset/4.jpg",
                "img_timestamp": "2021-03-10T00:00:00"
            },
        ]
    },
    {
        "first_name": "Winston",
        "last_name": "Rogers",
        "date_of_birth": "1970-04-04",
        "images_lst": [
            {
                "img_uri": "img_dataset/2.jpg",
                "img_timestamp": "2020-06-15T00:00:00"
            }
        ]
    },
    {
        "first_name": "Diane",
        "last_name": "Simmons",
        "date_of_birth": "1980-08-01",
        "images_lst": [
            {
                "img_uri": "img_dataset/3.jpg",
                "img_timestamp": "2020-03-14T00:00:00"
            }
        ]
    }
]


async def populate_fixtures(db_client, s3_client):
    """
    Checks if the database is empty and if so populates it with the predefined fixtures from this file
    (see `FIXTURE_DATA` in this file for data).
    """
    if await db_client.patients.estimated_document_count():
        # This database has been populated so no need to re-init with fixture data
        return
    else:
        for entity_data in FIXTURE_DATA:
            img_lst = entity_data.get("images_lst", [])
            # This step of parsing into the pydanctic model below ensures the data/schema integrity
            # so even though we get back to dict post this, it is useful
            patient = models.Patient.model_validate(entity_data)
            patient_data = patient.model_dump(by_alias=True)
            patient_data["date_of_birth"] = datetime.datetime.combine(patient_data["date_of_birth"], datetime.time.min)
            new_patient = await db_client.patients.insert_one(patient_data)
            entity_data["id"] = str(new_patient.inserted_id)
            entity_data["images"] = []
            for img_obj in img_lst:
                img_obj = img_obj.copy()
                p = pathlib.Path(img_obj['img_uri'])
                img_timestamp_with_suffix = f"{img_obj['img_timestamp']}{p.suffix}"
                with open(pathlib.Path(__file__).parent.resolve()/p, "rb") as f:
                    s3_client.upload_fileobj(
                        f, os.environ["PATIENT_IMG_BUCKET"], f"{new_patient.inserted_id}/{img_timestamp_with_suffix}"
                    )
                    # populating the global object with the object storage uris and such enables better testing
                    img_obj["img_uri"] = f"{os.environ['PATIENT_IMG_BUCKET']}/{new_patient.inserted_id}/{img_timestamp_with_suffix}"
                entity_data["images"].append(img_obj)
