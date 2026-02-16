import os

import pytest
from fastapi.testclient import TestClient

# Ensure JWT secret exists during tests.
os.environ.setdefault("JWT_SECRET", "test_secret")


@pytest.fixture(scope="session")
def client():
    from src.api.main import app

    with TestClient(app) as c:
        yield c
