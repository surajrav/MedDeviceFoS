#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/30/2024
# FoS for Intuitive Surgical
import os
import pytest
import pytest_asyncio
from ... import utils


@pytest.mark.usefixtures("basic_crud")
@pytest_asyncio.fixture(scope="function", autouse=True)
async def basic_crud():

    # Test setup
    # hijack os env for database name and replace with test database name
    orig_db_name = os.environ.get("DB_NAME")
    os.environ["DB_NAME"] = os.environ.get("TEST_DB_NAME")
    db_client, db_handle = await utils.get_mongodb_connection(db_name=os.environ['TEST_DB_NAME'])
    await db_handle.drop_collection("patients")

    await db_handle.create_collection("patients", capped=False)

    # Yield and perform tests
    yield db_client, db_handle

    # for teardown restore the env var for the db name as well as shutdown the db client connection
    await db_handle.drop_collection("patients")
    db_client.close()
    os.environ["DB_NAME"] = orig_db_name
