"""
MedIntel AI — Backend Tests: Health Endpoint & Application Startup.

Phase 2 tests verify:
    1. The FastAPI application can be created.
    2. GET /health returns HTTP 200.
    3. The health response has the expected structure.
    4. The database tables can be created.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


# -------------------------------------------------------------------
# Application Startup Tests
# -------------------------------------------------------------------

class TestApplicationStartup:
    """Verify that the FastAPI application initializes correctly."""

    def test_app_is_created(self) -> None:
        """The FastAPI application instance should exist."""
        assert app is not None

    def test_app_title(self) -> None:
        """The application title should be set correctly."""
        assert app.title == "MedIntel AI"

    def test_app_version(self) -> None:
        """The application version should be set."""
        assert app.version == "0.1.0"


# -------------------------------------------------------------------
# Health Endpoint Tests
# -------------------------------------------------------------------

class TestHealthEndpoint:
    """Verify the GET /health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """GET /health should return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client: TestClient) -> None:
        """GET /health should return all expected fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "application" in data
        assert "environment" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        """GET /health should report status as 'healthy'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_application_name(self, client: TestClient) -> None:
        """GET /health should return the correct application name."""
        response = client.get("/health")
        data = response.json()
        assert data["application"] == "MedIntel AI"

    def test_health_version_matches(self, client: TestClient) -> None:
        """GET /health version should match the app version."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "0.1.0"

    def test_health_timestamp_is_present(self, client: TestClient) -> None:
        """GET /health should return a non-empty timestamp."""
        response = client.get("/health")
        data = response.json()
        assert data["timestamp"]
        assert len(data["timestamp"]) > 0


# -------------------------------------------------------------------
# Database Schema Tests
# -------------------------------------------------------------------

class TestDatabaseSchema:
    """Verify that the database tables can be created."""

    def test_create_tables(self, tmp_path) -> None:
        """All ORM model tables should be creatable without errors."""
        from sqlalchemy import create_engine, inspect
        from app.db.session import Base

        # Import models so they register with Base.metadata
        import app.models.models  # noqa: F401

        db_path = tmp_path / "test.db"
        test_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(bind=test_engine)

        inspector = inspect(test_engine)
        table_names = inspector.get_table_names()

        expected_tables = [
            "users",
            "reports",
            "test_results",
            "predictions",
            "prescriptions",
            "medicines",
            "summaries",
        ]
        for table in expected_tables:
            assert table in table_names, f"Table '{table}' was not created"

    def test_table_count(self, tmp_path) -> None:
        """Exactly 7 tables should be created."""
        from sqlalchemy import create_engine, inspect
        from app.db.session import Base

        import app.models.models  # noqa: F401

        db_path = tmp_path / "test.db"
        test_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(bind=test_engine)

        inspector = inspect(test_engine)
        table_names = inspector.get_table_names()
        assert len(table_names) == 7
