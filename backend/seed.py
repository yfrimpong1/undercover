"""Reset the database to UnderCover's records in data/: `uv run -m backend.seed`."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from backend.db import connect

DATA = Path(__file__).parent.parent / "data"


def read(name: str) -> Any:
    """Read one of the JSON files in data/."""
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed(db: sqlite3.Connection) -> str:
    """Replace everything in the database with the records in data/."""
    claims = read("claims.json")
    policies = read("policies.json")
    customers = read("customers.json")
    plans = read("plans.json")
    handlers = read("handlers.json")
    company = read("company.json")
    wording = {
        "version": company["policy_wording_version"],
        "text": (DATA / "policy_wording.md").read_text(encoding="utf-8"),
    }
    records = [
        *[("policy", policy["policy_id"], policy) for policy in policies],
        *[("customer", customer["customer_id"], customer) for customer in customers],
        *[("plan", plan["plan"], plan) for plan in plans["plans"]],
        *[("add_on", add_on["add_on"], add_on) for add_on in plans["add_ons"]],
        *[("handler", handler["handler_id"], handler) for handler in handlers],
        ("company", "company", company),
        ("wording", "policy_wording", wording),
    ]
    db.execute("DELETE FROM steps")
    db.execute("DELETE FROM claims")
    db.execute("DELETE FROM records")
    db.executemany(
        "INSERT INTO records (kind, id, data) VALUES (?, ?, ?)",
        [(kind, record_id, json.dumps(data)) for kind, record_id, data in records],
    )
    db.executemany(
        "INSERT INTO claims (claim_id, data, status) VALUES (?, ?, 'waiting')",
        [
            (
                claim["claim_id"],
                json.dumps({k: v for k, v in claim.items() if k != "status"}),
            )
            for claim in claims
        ],
    )
    return (
        f"Seeded {len(claims)} claims, {len(policies)} policies, "
        f"{len(customers)} customers, {len(plans['plans'])} plans "
        f"and {len(handlers)} handlers."
    )


def seed_if_empty(db: sqlite3.Connection) -> None:
    """Seed the database if it has no claims yet."""
    if db.execute("SELECT 1 FROM claims LIMIT 1").fetchone() is None:
        seed(db)


def main() -> None:
    """Reset the database and say what it holds."""
    with closing(connect()) as db, db:
        print(seed(db))


if __name__ == "__main__":
    main()
