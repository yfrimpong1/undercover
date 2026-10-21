"""The operations that read UnderCover's records."""

import sqlite3

from fastapi import APIRouter

from backend.db import Db, get_record, list_records
from backend.models import Customer, Handler, Policy, PolicyWording, PreviousClaim

router = APIRouter(prefix="/api")


def wording_sections(db: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    """Map each section number of the policy wording to its title and text."""
    text = get_record(db, "wording", "policy_wording")["text"]
    sections = {}
    for chunk in text.split("\n## ")[1:]:
        title, _, body = chunk.partition("\n")
        sections[int(title.split(".")[0])] = (title, body.strip())
    return sections


@router.get("/policies/{policy_id}", operation_id="get_policy")
def get_policy(policy_id: str, db: Db) -> Policy:
    """Get a policy with its plan's limits and its add-ons."""
    policy = get_record(db, "policy", policy_id)
    return Policy.model_validate(
        policy
        | {
            "plan": get_record(db, "plan", policy["plan"]),
            "add_ons": [get_record(db, "add_on", a) for a in policy["add_ons"]],
        }
    )


@router.get("/customers/{customer_id}", operation_id="get_customer")
def get_customer(customer_id: str, db: Db) -> Customer:
    """Get a customer's contact details and earlier claims."""
    return Customer.model_validate(get_record(db, "customer", customer_id))


@router.get("/customers/{customer_id}/claim-history", operation_id="get_claim_history")
def get_claim_history(customer_id: str, db: Db) -> list[PreviousClaim]:
    """Get a customer's earlier claims, without their personal details."""
    customer = get_record(db, "customer", customer_id)
    return [PreviousClaim.model_validate(c) for c in customer["previous_claims"]]


@router.get("/policy-wording", operation_id="get_policy_wording")
def get_policy_wording(db: Db) -> PolicyWording:
    """Get the policy wording that decisions follow."""
    return PolicyWording.model_validate(get_record(db, "wording", "policy_wording"))


@router.get("/handlers", operation_id="list_handlers")
def list_handlers(db: Db) -> list[Handler]:
    """List the claims handlers."""
    return [Handler.model_validate(h) for h in list_records(db, "handler")]
