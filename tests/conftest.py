import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


SQLITE_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    # Create the tables
    Base.metadata.create_all(bind=engine)
    
    # Run the test
    yield
    
    # Drop the tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
