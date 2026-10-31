import os
import sys
import pytest
import pytest_asyncio

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.core.config import settings
settings.APP_ENV = "test"

from backend.app.core.database import init_db

@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_test_db():
    await init_db()
    yield
