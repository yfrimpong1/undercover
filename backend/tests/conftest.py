from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from backend.db import connect
from backend.main import app
from backend.seed import seed


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    """Point every test at a database of its own."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))


@pytest.fixture
def client():
    """A client for a backend seeded from data/."""
    with closing(connect()) as db, db:
        seed(db)
    return TestClient(app)
