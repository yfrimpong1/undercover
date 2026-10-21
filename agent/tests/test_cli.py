import pytest

from agent import __main__ as cli


def decline(api):
    """A stand-in for the agent that declines each claim it's given."""
    worked = []

    def run(claim_id, thread_id):
        worked.append(claim_id)
        api.post(f"/api/claims/{claim_id}/start")
        api.post(
            f"/api/claims/{claim_id}/decision",
            json={
                "decision": "decline",
                "payout": 0,
                "reason": "Not covered.",
                "policy_section": 9,
            },
        )
        return "Declined."

    return run, worked


def test_the_queue_works_waiting_and_in_progress_claims(api, monkeypatch, capsys):
    run, worked = decline(api)
    run("CLM-1001", "earlier")
    api.post("/api/claims/CLM-1002/start")
    worked.clear()
    monkeypatch.setattr(cli, "run", run)
    cli.main([])
    assert worked == [f"CLM-{n}" for n in range(1002, 1026)]
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "CLM-1002: decline"
    assert len(lines) == 24


def test_one_claim(api, monkeypatch, capsys):
    run, worked = decline(api)
    monkeypatch.setattr(cli, "run", run)
    cli.main(["CLM-1004"])
    assert worked == ["CLM-1004"]
    assert capsys.readouterr().out == "CLM-1004: decline\n"


def test_a_decided_claim(api, monkeypatch, capsys):
    run, worked = decline(api)
    run("CLM-1001", "earlier")
    monkeypatch.setattr(cli, "run", run)
    cli.main(["CLM-1001"])
    assert worked == ["CLM-1001"]
    assert capsys.readouterr().out == "CLM-1001 is already decided.\n"


def test_an_unknown_claim(api, capsys):
    cli.main(["CLM-9999"])
    assert capsys.readouterr().out == "Claim CLM-9999 not found.\n"


def approved(status, payment):
    return {
        "claim_id": "CLM-1003",
        "status": status,
        "decision": {"decision": "approve", "payout": 1500.0},
        "payment": payment,
    }


@pytest.mark.parametrize(
    ("claim", "line"),
    [
        (
            {"claim_id": "CLM-1001", "decision": None},
            "CLM-1001 ended without a decision.",
        ),
        (
            approved("decided", {"amount": 1500.0}),
            "CLM-1003: approve, $1,500.00, paid",
        ),
        (
            approved("waiting_for_sign_off", None),
            "CLM-1003: approve, $1,500.00, waiting for sign-off",
        ),
        (approved("decided", None), "CLM-1003: approve, $1,500.00, not paid"),
    ],
)
def test_outcome(claim, line):
    assert cli.outcome(claim) == line
