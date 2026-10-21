import json
from contextlib import closing
from pathlib import Path

import pytest

from backend.db import connect

OVER_LIMIT = "A payout over $1,000.00 needs a handler's sign-off"


def decide(client, claim_id, decision="approve", payout=0.0, section=3):
    return client.post(
        f"/api/claims/{claim_id}/decision",
        json={
            "decision": decision,
            "payout": payout,
            "reason": "The reason.",
            "policy_section": section,
        },
    )


def approve(client, claim_id, payout, section=3):
    client.post(f"/api/claims/{claim_id}/start")
    return decide(client, claim_id, "approve", payout, section)


def pay(client, claim_id, amount):
    return client.post(f"/api/claims/{claim_id}/payment", json={"amount": amount})


def sign_off(client, claim_id, handler_id):
    return client.post(
        f"/api/claims/{claim_id}/sign-off", json={"handler_id": handler_id}
    )


def step(client, claim_id, kind="message", name="agent", content="Hello"):
    return client.post(
        f"/api/claims/{claim_id}/steps",
        json={"kind": kind, "name": name, "content": content},
    )


def test_get_instructions(client):
    text = Path("backend/instructions.md").read_text(encoding="utf-8")
    assert client.get("/api/instructions").json() == {"text": text}


def test_start_claim(client):
    claim = client.post("/api/claims/CLM-1001/start").json()
    assert claim["status"] == "in_progress"
    assert claim["started_at"]


def test_starting_again_clears_the_steps(client):
    client.post("/api/claims/CLM-1001/start")
    step(client, "CLM-1001")
    client.post("/api/claims/CLM-1001/start")
    assert client.get("/api/claims/CLM-1001/steps").json() == []
    assert client.get("/api/claims/CLM-1001").json()["status"] == "in_progress"


@pytest.mark.parametrize("payout", [420.0, 1500.0])
def test_a_claim_with_a_decision_cannot_start_again(client, payout):
    approve(client, "CLM-1003", payout, 7)
    response = client.post("/api/claims/CLM-1003/start")
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1003 already has a decision"}


def test_record_and_list_steps(client):
    client.post("/api/claims/CLM-1001/start")
    step(client, "CLM-1001", "tool_call", "get_claim", '{"claim_id": "CLM-1001"}')
    recorded = step(client, "CLM-1001", "tool_result", "get_claim", "{}").json()
    assert recorded["kind"] == "tool_result"
    assert recorded["created_at"]
    steps = client.get("/api/claims/CLM-1001/steps").json()
    assert [(s["kind"], s["name"]) for s in steps] == [
        ("tool_call", "get_claim"),
        ("tool_result", "get_claim"),
    ]
    assert steps[0]["step_id"] < steps[1]["step_id"]


def test_an_unknown_kind_of_step(client):
    client.post("/api/claims/CLM-1001/start")
    assert step(client, "CLM-1001", kind="thought").status_code == 422


def test_steps_need_a_started_claim(client):
    response = step(client, "CLM-1001")
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 hasn't been started"}


def test_steps_after_the_decision(client):
    approve(client, "CLM-1001", 420.0)
    assert step(client, "CLM-1001").status_code == 200


def test_steps_of_an_unknown_claim(client):
    assert client.get("/api/claims/CLM-9999/steps").status_code == 404


def test_deciding_needs_a_started_claim(client):
    response = decide(client, "CLM-1001", "approve", 420.0)
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 isn't in progress"}


def test_approve(client):
    claim = approve(client, "CLM-1001", 420.0).json()
    assert claim["status"] == "decided"
    decision = claim["decision"]
    assert decision["decision"] == "approve"
    assert decision["payout"] == 420.0
    assert decision["reason"] == "The reason."
    assert decision["policy_section"] == 3
    assert decision["policy_section_title"] == "3. Trip Delay"
    assert decision["policy_section_text"].startswith("We pay when your carrier")
    assert claim["payment"] is None
    assert decide(client, "CLM-1001", "approve", 420.0).status_code == 409


@pytest.mark.parametrize(
    ("decision", "payout", "section", "detail"),
    [
        ("decline", 10.0, 3, "A decline or a referral pays $0.00"),
        ("refer", 10.0, 3, "A decline or a referral pays $0.00"),
        ("approve", 420.01, 3, "The payout is more than the $420.00 claimed"),
        ("approve", 100.0, 13, "The policy wording has no section 13"),
    ],
)
def test_invalid_decisions(client, decision, payout, section, detail):
    client.post("/api/claims/CLM-1001/start")
    response = decide(client, "CLM-1001", decision, payout, section)
    assert response.status_code == 422
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("payout", [-1.0, 10.125])
def test_invalid_amounts(client, payout):
    client.post("/api/claims/CLM-1001/start")
    assert decide(client, "CLM-1001", "approve", payout).status_code == 422
    assert pay(client, "CLM-1001", payout).status_code == 422


def test_an_empty_reason(client):
    client.post("/api/claims/CLM-1001/start")
    response = client.post(
        "/api/claims/CLM-1001/decision",
        json={"decision": "decline", "payout": 0, "reason": "", "policy_section": 9},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("decision", ["decline", "refer"])
def test_decline_and_refer(client, decision):
    client.post("/api/claims/CLM-1001/start")
    claim = decide(client, "CLM-1001", decision, 0.0, 9).json()
    assert claim["status"] == "decided"
    assert claim["decision"]["decision"] == decision
    response = pay(client, "CLM-1001", 0.0)
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 has no approved payout"}


def test_pay(client):
    approve(client, "CLM-1001", 420.0)
    claim = pay(client, "CLM-1001", 420.0).json()
    assert claim["payment"]["amount"] == 420.0
    assert claim["payment"]["paid_at"]
    response = pay(client, "CLM-1001", 420.0)
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 is already paid"}


def test_pay_a_different_amount(client):
    approve(client, "CLM-1001", 420.0)
    response = pay(client, "CLM-1001", 400.0)
    assert response.status_code == 409
    assert response.json() == {"detail": "The approved payout is $420.00"}


def test_pay_an_undecided_claim(client):
    client.post("/api/claims/CLM-1001/start")
    assert pay(client, "CLM-1001", 420.0).status_code == 409


def test_a_payout_over_the_limit_is_blocked(client):
    claim = approve(client, "CLM-1003", 1500.0, 7).json()
    assert claim["status"] == "waiting_for_sign_off"
    response = pay(client, "CLM-1003", 1500.0)
    assert response.status_code == 403
    assert response.json() == {"detail": OVER_LIMIT}
    assert client.get("/api/claims/CLM-1003").json()["payment"] is None


def test_a_payout_of_exactly_the_limit(client):
    claim = approve(client, "CLM-1002", 1000.0, 5).json()
    assert claim["status"] == "decided"
    assert pay(client, "CLM-1002", 1000.0).json()["payment"]["amount"] == 1000.0


def test_sign_off_pays(client):
    approve(client, "CLM-1003", 1500.0, 7)
    claim = sign_off(client, "CLM-1003", "HND-01").json()
    assert claim["status"] == "decided"
    assert claim["sign_off"]["handler_id"] == "HND-01"
    assert claim["sign_off"]["handler_name"] == "Dana Whitfield"
    assert claim["payment"]["amount"] == 1500.0
    assert claim["payment"]["paid_at"] == claim["sign_off"]["signed_off_at"]
    assert sign_off(client, "CLM-1003", "HND-01").status_code == 409
    assert pay(client, "CLM-1003", 1500.0).status_code == 409


def test_sign_off_needs_a_claim_waiting_for_it(client):
    approve(client, "CLM-1001", 420.0)
    response = sign_off(client, "CLM-1001", "HND-01")
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 isn't waiting for sign-off"}


def test_sign_off_by_an_unknown_handler(client):
    approve(client, "CLM-1003", 1500.0, 7)
    response = sign_off(client, "CLM-1003", "HND-99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Handler HND-99 not found"}


def test_sign_off_by_a_handler_who_cannot(client):
    handler = {
        "handler_id": "HND-09",
        "name": "Sam Trainee",
        "role": "Trainee",
        "email": "sam@undercover.example",
        "can_approve_over_limit": False,
    }
    with closing(connect()) as db, db:
        db.execute(
            "INSERT INTO records VALUES ('handler', 'HND-09', ?)",
            (json.dumps(handler),),
        )
    approve(client, "CLM-1003", 1500.0, 7)
    response = sign_off(client, "CLM-1003", "HND-09")
    assert response.status_code == 403
    assert response.json() == {"detail": "Sam Trainee can't sign off over $1,000.00"}
    assert client.get("/api/claims/CLM-1003").json()["payment"] is None


def test_the_queue_shows_decisions(client):
    approve(client, "CLM-1001", 420.0)
    pay(client, "CLM-1001", 420.0)
    approve(client, "CLM-1003", 1500.0, 7)
    claims = {c["claim_id"]: c for c in client.get("/api/claims").json()}
    assert claims["CLM-1001"]["decision"] == "approve"
    assert claims["CLM-1001"]["payout"] == 420.0
    assert claims["CLM-1001"]["paid"] is True
    assert claims["CLM-1003"]["status"] == "waiting_for_sign_off"
    assert claims["CLM-1003"]["paid"] is False
