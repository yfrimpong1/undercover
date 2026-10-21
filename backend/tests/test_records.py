from contextlib import closing

from backend.db import connect
from backend.records import wording_sections


def test_get_policy_with_its_plan(client):
    policy = client.get("/api/policies/POL-2001").json()
    assert policy["plan"]["name"] == "UnderCover Premium"
    assert policy["plan"]["trip_delay_max"] == 800.0
    assert policy["plan"]["deductible"] == 50.0
    assert policy["trip"] == {
        "destination": "Rome, Italy",
        "departs_on": "2026-06-10",
        "returns_on": "2026-06-18",
        "trip_cost": 3100.0,
    }
    assert policy["travelers"] == ["Maya Patel"]
    assert policy["add_ons"] == []


def test_get_policy_with_an_add_on(client):
    policy = client.get("/api/policies/POL-2009").json()
    assert policy["add_ons"] == [
        {"add_on": "electronics_plus", "name": "Electronics Plus"}
    ]


def test_unknown_policy(client):
    response = client.get("/api/policies/POL-9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Policy POL-9999 not found"}


def test_get_customer(client):
    customer = client.get("/api/customers/CUS-3001").json()
    assert customer["name"] == "Maya Patel"
    assert customer["email"] == "maya.patel@example.com"
    assert [c["claim_id"] for c in customer["previous_claims"]] == ["CLM-0412"]


def test_claim_history_has_no_personal_details(client):
    history = client.get("/api/customers/CUS-3001/claim-history").json()
    assert [c["claim_id"] for c in history] == ["CLM-0412"]
    fields = set(history[0])
    assert fields.isdisjoint({"name", "email", "phone", "date_of_birth", "address"})


def test_unknown_customer(client):
    response = client.get("/api/customers/CUS-9999/claim-history")
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer CUS-9999 not found"}


def test_get_policy_wording(client):
    wording = client.get("/api/policy-wording").json()
    assert wording["version"] == "2026.1"
    assert wording["text"].startswith("# UnderCover Travel Insurance: Policy Wording")


def test_wording_sections(client):
    with closing(connect()) as db:
        sections = wording_sections(db)
    assert list(sections) == list(range(1, 13))
    title, text = sections[3]
    assert title == "3. Trip Delay"
    assert text.startswith("We pay when your carrier delays you")


def test_list_handlers(client):
    handlers = client.get("/api/handlers").json()
    assert [h["name"] for h in handlers] == [
        "Dana Whitfield",
        "Marcus Oyelaran",
        "Priya Raman",
    ]
