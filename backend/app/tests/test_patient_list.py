#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/30/2024
# FoS for Intuitive Surgical
import pytest
from .. import fixtures


pytestmark = pytest.mark.asyncio(scope="function")


class TestPatientList:

    @pytest.mark.parametrize(
        'count',
        [len(fixtures.FIXTURE_DATA)],
        ids=[
            "GET Patient List: verify bootstrapped count of patients",
        ]
    )
    async def test_patients_bootstrapped_overall_count(self, count, client):
        """
        Test that the total number of bootstrapped patients is the same as that inserted
        """
        # Hit the endpoint
        response = await client.get('/patients')

        # Assert success
        assert response.status_code == 200

        # Assert we get back the expected count for this list test
        data = response.json()

        assert len(data['patients']) == count

    async def test_patients_list_data(self, client):
        """
        Test that the patient list contains all the bootstrapped initial list of patient names.
        """
        # Hit the endpoint
        response = await client.get('/patients')

        # Assert success
        assert response.status_code == 200

        # Assert we get back the expected count for this list test
        data = response.json()

        list_keys = ["id", "first_name", "last_name"]
        actual_patients_data = sorted(fixtures.FIXTURE_DATA, key=lambda x: x['first_name'])
        actual_patients_data = [{key: patient_entity[key] for key in list_keys} for patient_entity in actual_patients_data]
        received_patients_data = sorted(data["patients"], key=lambda x: x['first_name'])

        assert received_patients_data == actual_patients_data
