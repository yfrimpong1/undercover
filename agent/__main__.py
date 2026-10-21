"""Work the queue: `uv run -m agent`, or one claim: `uv run -m agent CLM-1001`."""

import sys
from typing import Any
from uuid import uuid4

from agent.main import backend, run

OPEN = {"waiting", "in_progress"}


def outcome(claim: dict[str, Any]) -> str:
    """Say in one line how the agent left a claim."""
    claim_id, decision = claim["claim_id"], claim["decision"]
    if decision is None:
        return f"{claim_id} ended without a decision."
    if decision["decision"] != "approve":
        return f"{claim_id}: {decision['decision']}"
    if claim["payment"]:
        payment = "paid"
    elif claim["status"] == "waiting_for_sign_off":
        payment = "waiting for sign-off"
    else:
        payment = "not paid"
    return f"{claim_id}: approve, ${decision['payout']:,.2f}, {payment}"


def work(claim_id: str) -> str:
    """Run the agent on one claim and say how it left it."""
    run(claim_id, uuid4().hex)
    with backend() as client:
        return outcome(client.get(f"/api/claims/{claim_id}").raise_for_status().json())


def main(claim_ids: list[str]) -> None:
    """Work the claims named, or every waiting or in-progress claim in order."""
    with backend() as client:
        claims = client.get("/api/claims").raise_for_status().json()
    statuses = {claim["claim_id"]: claim["status"] for claim in claims}
    for claim_id in claim_ids or [c for c, s in statuses.items() if s in OPEN]:
        if claim_id not in statuses:
            print(f"Claim {claim_id} not found.")
        elif statuses[claim_id] in OPEN:
            print(work(claim_id), flush=True)
        else:
            print(f"{claim_id} is already decided.")


if __name__ == "__main__":
    main(sys.argv[1:])
