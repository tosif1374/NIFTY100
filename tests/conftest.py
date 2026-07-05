import sys
from pathlib import Path
import sqlite3
import pytest
from unittest.mock import patch
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from src.api.auth import create_access_token

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture
def mock_db_for_test(request):
    """Provides a context manager to patch get_connection for tests."""
    def _mock_get_connection(test_db_path):
        def mock_get_conn(db_path=None):
            conn = sqlite3.connect(f"file:{test_db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        return mock_get_conn
    return _mock_get_connection

@pytest.fixture(scope="session")
def valid_token() -> str:
    """JWT token for the demo 'analyst' user — valid for the whole test session."""
    return create_access_token({"sub": "analyst", "role": "read"})

@pytest.fixture(scope="session")
def auth_headers(valid_token) -> dict:
    return {"Authorization": f"Bearer {valid_token}"}

@pytest_asyncio.fixture(scope="session")
async def client():
    """Shared async httpx client connected to the FastAPI test app."""
    async with AsyncClient(
transport=ASGITransport(app=app),
base_url="http://test"
) as ac:
        yield ac