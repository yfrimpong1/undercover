import json
from contextlib import closing

from fastapi.testclient import TestClient

from backend import seed
from backend.db import connect
from backend.main import app


def test_seed_says_what_it_loaded():
    with closing(connect()) as db, db:
        message = seed.seed(db)
    assert message == (
        "Seeded 25 claims, 50 policies, 49 customers, 3 plans and 3 handlers."
    )


def test_seed_resets_the_claims():
    with closing(connect()) as db, db:
        seed.seed(db)
        db.execute("UPDATE claims SET status = 'decided'")
        seed.seed(db)
        statuses = {row[0] for row in db.execute("SELECT status FROM claims")}
    assert statuses == {"waiting"}


def test_claims_keep_their_status_out_of_the_record():
    with closing(connect()) as db, db:
        seed.seed(db)
        data = json.loads(db.execute("SELECT data FROM claims").fetchone()[0])
    assert "status" not in data


def test_the_backend_seeds_an_empty_database_on_startup():
    with TestClient(app) as client:
        assert len(client.get("/api/claims").json()) == 25


def test_a_restart_keeps_the_data(client):
    client.post("/api/claims/CLM-1001/start")
    with closing(connect()) as db, db:
        db.execute("UPDATE claims SET status = 'decided' WHERE claim_id = 'CLM-1001'")
    with TestClient(app) as restarted:
        assert restarted.get("/api/claims/CLM-1001").json()["status"] == "decided"


def test_main_prints_what_it_seeded(capsys):
    seed.main()
    assert capsys.readouterr().out.startswith("Seeded 25 claims")
