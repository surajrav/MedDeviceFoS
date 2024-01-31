#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/30/2024
# FoS for Intuitive Surgical


pytest_plugins = [
    "app.tests.test_fixtures.fixture_s3_client",
    "app.tests.test_fixtures.fixture_db_crud",
    "app.tests.test_fixtures.fixture_app_client"
]
