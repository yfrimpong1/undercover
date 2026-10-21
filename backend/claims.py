"""The operations on claims."""

import json
import sqlite3

from fastapi import APIRouter, HTTPException

from backend.db import Db, get_record, list_records, now
from backend.models import (
    Claim,
    ClaimSummary,
    Decision,
    DecisionIn,
    Payment,
    PaymentIn,
    SignOff,
    SignOffIn,
    Step,
    StepIn,
)
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


def approval_limit(db: sqlite3.Connection) -> float:
    """Return the payout over which a handler must sign off."""
    return get_record(db, "company", "company")["payout_approval_limit"]


def money(amount: float) -> str:
    """Write an amount in US dollars, such as $1,250.00."""
    return f"${amount:,.2f}"


@router.post("/{claim_id}/start", operation_id="start_claim")
def start_claim(claim_id: str, db: Db) -> Claim:
    """Start work on a claim, clearing the steps of any earlier run."""
    if load_claim(db, claim_id)["status"] not in {"waiting", "in_progress"}:
        raise HTTPException(409, f"{claim_id} already has a decision")
    db.execute("DELETE FROM steps WHERE claim_id = ?", (claim_id,))
    db.execute(
        "UPDATE claims SET status = 'in_progress', started_at = ? WHERE claim_id = ?",
        (now(), claim_id),
    )
    return to_claim(db, load_claim(db, claim_id))


@router.post("/{claim_id}/steps", operation_id="record_step")
def record_step(claim_id: str, step: StepIn, db: Db) -> Step:
    """Record one step of the agent's work on a claim."""
    if load_claim(db, claim_id)["status"] == "waiting":
        raise HTTPException(409, f"{claim_id} hasn't been started")
    row = db.execute(
        "INSERT INTO steps (claim_id, kind, name, content, created_at) "
        "VALUES (?, ?, ?, ?, ?) RETURNING step_id, kind, name, content, created_at",
        (claim_id, step.kind, step.name, step.content, now()),
    ).fetchone()
    return Step.model_validate(dict(row))


@router.get("/{claim_id}/steps", operation_id="list_steps")
def list_steps(claim_id: str, db: Db) -> list[Step]:
    """List the agent's steps on a claim, in order."""
    load_claim(db, claim_id)
    rows = db.execute(
        "SELECT step_id, kind, name, content, created_at FROM steps "
        "WHERE claim_id = ? ORDER BY step_id",
        (claim_id,),
    )
    return [Step.model_validate(dict(row)) for row in rows]


def check_decision(
    db: sqlite3.Connection, amount_claimed: float, decision: DecisionIn
) -> None:
    """Raise 422 if a decision breaks the rules for payouts and sections."""
    if decision.decision != "approve" and decision.payout != 0:
        raise HTTPException(422, "A decline or a referral pays $0.00")
    if decision.payout > amount_claimed:
        claimed = money(amount_claimed)
        raise HTTPException(422, f"The payout is more than the {claimed} claimed")
    if decision.policy_section not in wording_sections(db):
        raise HTTPException(
            422, f"The policy wording has no section {decision.policy_section}"
        )


@router.post("/{claim_id}/decision", operation_id="decide_claim")
def decide_claim(claim_id: str, decision: DecisionIn, db: Db) -> Claim:
    """Record the decision on a claim: approve with a payout, decline or refer."""
    row = load_claim(db, claim_id)
    if row["status"] != "in_progress":
        raise HTTPException(409, f"{claim_id} isn't in progress")
    check_decision(db, json.loads(row["data"])["amount_claimed"], decision)
    payout = float(decision.payout)
    over_limit = decision.decision == "approve" and payout > approval_limit(db)
    db.execute(
        "UPDATE claims SET status = ?, decision = ?, payout = ?, reason = ?, "
        "policy_section = ?, decided_at = ? WHERE claim_id = ?",
        (
            "waiting_for_sign_off" if over_limit else "decided",
            decision.decision,
            payout,
            decision.reason,
            decision.policy_section,
            now(),
            claim_id,
        ),
    )
    return to_claim(db, load_claim(db, claim_id))


@router.post("/{claim_id}/payment", operation_id="pay_claim")
def pay_claim(claim_id: str, payment: PaymentIn, db: Db) -> Claim:
    """Pay a claim's approved payout, which over the limit needs a sign-off first."""
    row = load_claim(db, claim_id)
    if row["decision"] != "approve":
        raise HTTPException(409, f"{claim_id} has no approved payout")
    if row["paid_at"] is not None:
        raise HTTPException(409, f"{claim_id} is already paid")
    if float(payment.amount) != row["payout"]:
        raise HTTPException(409, f"The approved payout is {money(row['payout'])}")
    limit = approval_limit(db)
    if row["payout"] > limit:
        raise HTTPException(
            403, f"A payout over {money(limit)} needs a handler's sign-off"
        )
    db.execute(
        "UPDATE claims SET paid_amount = payout, paid_at = ? WHERE claim_id = ?",
        (now(), claim_id),
    )
    return to_claim(db, load_claim(db, claim_id))


@router.post("/{claim_id}/sign-off", operation_id="sign_off_claim")
def sign_off_claim(claim_id: str, sign_off: SignOffIn, db: Db) -> Claim:
    """Sign off a payout over the limit as a handler, which pays it."""
    if load_claim(db, claim_id)["status"] != "waiting_for_sign_off":
        raise HTTPException(409, f"{claim_id} isn't waiting for sign-off")
    handler = get_record(db, "handler", sign_off.handler_id)
    if not handler["can_approve_over_limit"]:
        limit = money(approval_limit(db))
        raise HTTPException(403, f"{handler['name']} can't sign off over {limit}")
    signed_off_at = now()
    db.execute(
        "UPDATE claims SET status = 'decided', signed_off_by = ?, signed_off_at = ?, "
        "paid_amount = payout, paid_at = ? WHERE claim_id = ?",
        (sign_off.handler_id, signed_off_at, signed_off_at, claim_id),
    )
    return to_claim(db, load_claim(db, claim_id))
