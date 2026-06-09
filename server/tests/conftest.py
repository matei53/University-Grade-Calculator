"""
Pytest configuration and fixtures for testing the API.
Provides in-memory SQLite database for testing and FastAPI test client.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from server.database import Base, get_db
from server.main import app


@pytest.fixture(scope="session")
def test_db_url():
    """Create a temporary database for testing."""
    # Use SQLite in-memory database for testing
    return "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a FastAPI test client with dependency override."""

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "testpassword123",
        "num_years": 3,
        "credit_requirements": [60, 60, 60],
    }


@pytest.fixture(scope="function")
def test_university(test_db):
    """Create a test university."""
    from server.models import University

    university = University(name="Test University")
    test_db.add(university)
    test_db.commit()
    test_db.refresh(university)
    return university


@pytest.fixture(scope="function")
def test_major(test_db):
    """Create a test major."""
    from server.models import Major

    major = Major(name="Computer Science")
    test_db.add(major)
    test_db.commit()
    test_db.refresh(major)
    return major


@pytest.fixture(scope="function")
def registered_user(client, test_user_data):
    """Register a test user and return the token."""
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    return {
        "token": data["access_token"],
        "username": test_user_data["username"],
    }


@pytest.fixture(scope="function")
def authenticated_headers(registered_user):
    """Return authorization headers with a valid token."""
    return {"Authorization": f"Bearer {registered_user['token']}"}
