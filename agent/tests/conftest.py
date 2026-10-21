from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from agent import __main__ as cli
from agent import main
from backend.db import connect
from backend.main import app
from backend.seed import seed


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    """Point every test at a database of its own."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))


@pytest.fixture
def api(monkeypatch):
    """Seed the backend and send the agent's calls to it in-process."""
    with closing(connect()) as db, db:
        seed(db)
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))
    monkeypatch.setattr(cli, "backend", lambda: TestClient(app))
    return TestClient(app)
