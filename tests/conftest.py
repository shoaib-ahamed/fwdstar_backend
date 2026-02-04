"""
Test configuration and fixtures.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Test database URL (in-memory SQLite for fast testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Create test database engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override get_db dependency for testing."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Apply database override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database and tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "SHIPPER"
    }


@pytest.fixture
def weak_password_user_data():
    """User data with weak password for testing."""
    return {
        "email": "weak@example.com",
        "password": "weak",  # Too short
        "role": "SHIPPER"
    }


@pytest.fixture
def invalid_role_user_data():
    """User data with invalid role for testing."""
    return {
        "email": "invalid@example.com",
        "password": "TestPass123",
        "role": "INVALID_ROLE"
    }


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="testuser@example.com",
        password="TestPass123",
        role="SHIPPER"
    )

    user = await UserService.create_user(db_session, user_data)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin test user."""
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="admin@example.com",
        password="AdminPass123",
        role="ADMIN"
    )

    user = await UserService.create_user(db_session, user_data)
    return user


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user):
    """Create an authenticated client with login."""
    from app.core.security import create_access_token, create_refresh_token

    # Create tokens
    access_token = create_access_token(
        data={"sub": test_user.id, "email": test_user.email, "role": test_user.role}
    )
    refresh_token = create_refresh_token(data={"sub": test_user.id})

    # Set cookies
    client.cookies.set("access_token", access_token)
    client.cookies.set("refresh_token", refresh_token)

    return client


@pytest.fixture
def locked_user_data():
    """User data for testing account locking."""
    return {
        "email": "locked@example.com",
        "password": "TestPass123",
        "role": "DRIVER"
    }
