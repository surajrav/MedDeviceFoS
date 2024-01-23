#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/20/2024
# FoS for Intuitive Surgical
import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Patient(BaseModel):
    # For the id part of this model see:
    # https://www.mongodb.com/developer/languages/python/farm-stack-fastapi-react-mongodb/
    id: str = Field(default_factory=uuid.uuid4, alias="_id", description="Patient ID which is generated by the system")
    first_name: str = Field(..., description="First name of the patient")
    last_name: str = Field(..., description="Last name of the patient")
    img_uri: Optional[str] = Field(None, description="Path suffix for this patient's medical image. Prefix with hosted website base url to use")
    date_of_birth: datetime.datetime = Field(..., description="ISO 8601 formatted timestamp of the patient's birth date")
    img_timestamp: Optional[datetime.datetime] = Field(None, description="ISO 8601 formatted timestamp indicating when the patient's medical image was taken")

    # for this part of "populate_by_name" see the following links:
    # https://www.mongodb.com/community/forums/t/why-do-we-need-alias-id-in-pydantic-model-of-fastapi/170728/3
    # https://www.mongodb.com/developer/languages/python/farm-stack-fastapi-react-mongodb/
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "id": "55d0bf24-e972-438f-9249-981134f041fb",
                "first_name": "Suraj",
                "last_name": "Ravichandran",
                "date_of_birth": "1986-09-18T11:55:00-07:00",
                "img_timestamp": "2024-01-22T08:02:48.263247Z"
            }
        },
    )


class PatientList(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id", description="Patient ID which is generated by the system")
    first_name: str = Field(..., description="First name of the patient")
    last_name: str = Field(..., description="Last name of the patient")


class PatientCollection(BaseModel):
    """
    A container holding a list of `StudentModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)

    (see https://www.mongodb.com/developer/languages/python/python-quickstart-fastapi/)
    """
    patients: list[PatientList]
