"""The operations on claims."""

import json
import sqlite3

from fastapi import APIRouter, HTTPException

from backend.db import Db, get_record, list_records
from backend.models import Claim, ClaimSummary, Decision, Payment, SignOff
from backend.records import wording_sections

router = APIRouter(prefix="/api/claims")


def load_claim(db: sqlite3.Connection, claim_id: str) -> sqlite3.Row:
    """Return a claim's row, or raise 404 if there isn't one."""
    row = db.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Claim {claim_id} not found")
    return row


def to_claim(db: sqlite3.Connection, row: sqlite3.Row) -> Claim:
    """Build the full claim from its row."""
    data = json.loads(row["data"])
    decision = payment = sign_off = None
    if row["decision"] is not None:
        title, text = wording_sections(db)[row["policy_section"]]
        decision = Decision(
            decision=row["decision"],
            payout=row["payout"],
            reason=row["reason"],
            policy_section=row["policy_section"],
            policy_section_title=title,
            policy_section_text=text,
            decided_at=row["decided_at"],
        )
    if row["paid_at"] is not None:
        payment = Payment(amount=row["paid_amount"], paid_at=row["paid_at"])
    if row["signed_off_by"] is not None:
        handler = get_record(db, "handler", row["signed_off_by"])
        sign_off = SignOff(
            handler_id=handler["handler_id"],
            handler_name=handler["name"],
            signed_off_at=row["signed_off_at"],
        )
    return Claim.model_validate(
        data
        | {
            "customer_name": get_record(db, "customer", data["customer_id"])["name"],
            "status": row["status"],
            "started_at": row["started_at"],
            "decision": decision,
            "payment": payment,
            "sign_off": sign_off,
        }
    )


@router.get("", operation_id="list_claims")
def list_claims(db: Db) -> list[ClaimSummary]:
    """List the claims queue with where each claim stands."""
    names = {c["customer_id"]: c["name"] for c in list_records(db, "customer")}
    claims = []
    for row in db.execute("SELECT * FROM claims ORDER BY claim_id"):
        data = json.loads(row["data"])
        claims.append(
            ClaimSummary(
                claim_id=row["claim_id"],
                customer_name=names[data["customer_id"]],
                claim_type=data["claim_type"],
                summary=data["summary"],
                submitted_on=data["submitted_on"],
                amount_claimed=data["amount_claimed"],
                status=row["status"],
                decision=row["decision"],
                payout=row["payout"],
                paid=row["paid_at"] is not None,
            )
        )
    return claims


@router.get("/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str, db: Db) -> Claim:
    """Get a claim in full: the story, items, documents and decision."""
    return to_claim(db, load_claim(db, claim_id))
