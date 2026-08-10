import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Append backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Override environment variables for the test suite before importing settings
os.environ["GITHUB_TOKEN"] = "test_github_token"
os.environ["GITHUB_APP_ID"] = "12345"
os.environ["GITHUB_PRIVATE_KEY"] = "test_private_key"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_API_KEY"] = "test_llm_key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SANDBOX_IMAGE"] = "python:3.10-slim"

from app.core.database import Base, get_db
from app.main import app

# Create in-memory engine and session for test runs
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def init_test_db() -> None:
    """
    Creates all tables in the SQLite in-memory database for the test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Provides a transactional database session for a single test.
    Rolls back any changes after test execution.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function", autouse=True)
def override_db_dependency(db_session) -> None:
    """
    Overrides the FastAPI database dependency for every test case.
    """
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Provides a FastAPI test client instance for integration testing.
    """
    with TestClient(app) as test_client:
        yield test_client
