import pytest


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    """Point every test at a database of its own."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
