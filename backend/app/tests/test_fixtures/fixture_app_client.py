#!/usr/bin/env python3
# Author: Suraj Ravichandran
# 01/30/2024
# FoS for Intuitive Surgical
import pytest_asyncio
import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from ...main import app


@pytest.mark.usefixtures("s3_client")
@pytest_asyncio.fixture(scope="function", autouse=True)
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as ac:
            yield ac
