"""The UnderCover database, in SQLite."""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, HTTPException

DEFAULT_PATH = Path(__file__).parent / "undercover.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    kind TEXT NOT NULL,
    id TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (kind, id)
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    decision TEXT,
    payout REAL,
    reason TEXT,
    policy_section INTEGER,
    decided_at TEXT,
    paid_amount REAL,
    paid_at TEXT,
    signed_off_by TEXT,
    signed_off_at TEXT
);
CREATE TABLE IF NOT EXISTS steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL REFERENCES claims (claim_id),
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    """Open the database in UNDERCOVER_DB, or backend/undercover.db by default."""
    path = os.getenv("UNDERCOVER_DB", str(DEFAULT_PATH))
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def get_db() -> Iterator[sqlite3.Connection]:
    """Give a request its own connection, committed when the request succeeds."""
    with closing(connect()) as connection, connection:
        yield connection


# "function" commits before the response goes out, so the next request sees it.
Db = Annotated[sqlite3.Connection, Depends(get_db, scope="function")]


def now() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def get_record(db: sqlite3.Connection, kind: str, record_id: str) -> dict[str, Any]:
    """Return one record, or raise 404 if there isn't one."""
    row = db.execute(
        "SELECT data FROM records WHERE kind = ? AND id = ?", (kind, record_id)
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"{kind.capitalize()} {record_id} not found")
    return json.loads(row["data"])


def list_records(db: sqlite3.Connection, kind: str) -> list[dict[str, Any]]:
    """Return every record of one kind, in id order."""
    rows = db.execute(
        "SELECT data FROM records WHERE kind = ? ORDER BY id", (kind,)
    ).fetchall()
    return [json.loads(row["data"]) for row in rows]
