import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

sys.path.insert(0, str(Path(__file__).parent.parent))

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/accos_test"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["LDAP_SERVER"] = "ldap://localhost:389"
os.environ["RATE_LIMITS_ENABLED"] = "false"

from app.core.dependencies import get_db
from app.db.base import Base
from main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker(bind=test_engine, expire_on_commit=False)() as s:
        async with s.begin():
            yield s


@pytest_asyncio.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db_override():
        async with async_sessionmaker(bind=test_engine, expire_on_commit=False)() as s:
            async with s.begin():
                yield s

    app.dependency_overrides[get_db] = _get_db_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    with patch("app.services.auth_service.AuthService._authenticate_ldap") as mock_auth:
        mock_auth.return_value = {
            "authenticated": True, "email": "admin@local",
            "full_name": "Admin", "groups": [],
        }
        res = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        return res.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client: AsyncClient) -> str:
    with patch("app.services.auth_service.AuthService._authenticate_ldap") as mock_auth:
        mock_auth.return_value = {
            "authenticated": True, "email": "user@local",
            "full_name": "Test User", "groups": [],
        }
        res = await client.post("/api/v1/auth/login", json={
            "username": "testuser", "password": "pass"
        })
        return res.json()["access_token"]
