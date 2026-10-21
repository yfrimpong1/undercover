from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from pydantic import Field

from agent import main

READS = ["get_claim", "get_policy", "get_claim_history", "get_policy_wording"]


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies and keeps what it was sent."""

    prompts: list = Field(default_factory=list)

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append(messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


def call(name, **args):
    return {"name": name, "args": args, "id": f"{name}-{len(args)}"}


def stub(*replies):
    return StubModel(messages=iter(replies))


def reads(claim_id, policy_id, customer_id):
    return AIMessage(
        content="",
        tool_calls=[
            call("get_claim", claim_id=claim_id),
            call("get_policy", policy_id=policy_id),
            call("get_claim_history", customer_id=customer_id),
            call("get_policy_wording"),
        ],
    )


def decision(kind, payout, section):
    return AIMessage(
        content="",
        tool_calls=[
            call(
                "decide_claim",
                decision=kind,
                payout=payout,
                reason="The reason.",
                policy_section=section,
            )
        ],
    )


def payment(amount):
    return AIMessage(content="", tool_calls=[call("pay_claim", amount=amount)])


def test_approve_and_pay(api):
    reply = main.run(
        "CLM-1001",
        "thread-1",
        stub(
            reads("CLM-1001", "POL-2001", "CUS-3001"),
            decision("approve", 420.0, 3),
            payment(420.0),
            AIMessage(content="Approved and paid $420.00."),
        ),
    )
    assert reply == "Approved and paid $420.00."
    claim = api.get("/api/claims/CLM-1001").json()
    assert claim["status"] == "decided"
    assert claim["decision"]["payout"] == 420.0
    assert claim["payment"]["amount"] == 420.0
    steps = [
        (s["kind"], s["name"]) for s in api.get("/api/claims/CLM-1001/steps").json()
    ]
    assert steps[:4] == [("tool_call", name) for name in READS]
    assert sorted(steps[4:8]) == sorted(("tool_result", name) for name in READS)
    assert steps[8:] == [
        ("tool_call", "decide_claim"),
        ("tool_result", "decide_claim"),
        ("tool_call", "pay_claim"),
        ("tool_result", "pay_claim"),
        ("message", "agent"),
    ]


def test_a_payout_over_the_limit_is_refused(api):
    main.run(
        "CLM-1003",
        "thread-1",
        stub(
            decision("approve", 1500.0, 7),
            payment(1500.0),
            AIMessage(content="The payment waits for a handler."),
        ),
    )
    claim = api.get("/api/claims/CLM-1003").json()
    assert claim["status"] == "waiting_for_sign_off"
    assert claim["payment"] is None
    result = api.get("/api/claims/CLM-1003/steps").json()[3]
    assert result["name"] == "pay_claim"
    assert "needs a handler's sign-off" in result["content"]


@pytest.mark.parametrize("kind", ["decline", "refer"])
def test_decline_and_refer(api, kind):
    main.run("CLM-1004", "thread-1", stub(decision(kind, 0.0, 4), AIMessage("Done.")))
    claim = api.get("/api/claims/CLM-1004").json()
    assert claim["status"] == "decided"
    assert claim["decision"]["decision"] == kind
    assert claim["payment"] is None


def test_the_system_prompt_is_the_instructions(api):
    model = stub(AIMessage(content="I need more time."))
    main.run("CLM-1001", "thread-1", model)
    system = model.prompts[0][0]
    assert isinstance(system, SystemMessage)
    assert system.content == Path("backend/instructions.md").read_text(encoding="utf-8")


def test_a_run_without_a_decision_leaves_the_claim_in_progress(api):
    main.run("CLM-1001", "thread-1", stub(AIMessage(content="I can't decide.")))
    assert api.get("/api/claims/CLM-1001").json()["status"] == "in_progress"


def test_deciding_and_paying_act_on_the_runs_claim():
    tools = {tool.name: tool for tool in main.claim_tools("CLM-1001")}
    assert set(tools) == {*READS, "decide_claim", "pay_claim"}
    assert set(tools["decide_claim"].args) == {
        "decision",
        "payout",
        "reason",
        "policy_section",
    }
    assert set(tools["pay_claim"].args) == {"amount"}


def test_tools_return_the_backends_errors(api):
    assert main.get_claim.invoke({"claim_id": "CLM-9999"}) == (
        '{"detail":"Claim CLM-9999 not found"}'
    )


def test_steps_of_a_message_with_text_and_a_tool_call():
    message = AIMessage(
        content="Reading the claim.", tool_calls=[call("get_claim", claim_id="X")]
    )
    assert main.steps(message) == [
        {"kind": "message", "name": "agent", "content": "Reading the claim."},
        {"kind": "tool_call", "name": "get_claim", "content": '{"claim_id": "X"}'},
    ]


def test_steps_of_a_tool_result():
    message = ToolMessage(content="{}", name="get_claim", tool_call_id="1")
    assert main.steps(message) == [
        {"kind": "tool_result", "name": "get_claim", "content": "{}"}
    ]


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"


def test_steps_keep_characters_as_written():
    message = AIMessage(
        content="", tool_calls=[call("decide_claim", reason="The plan’s limit")]
    )
    assert main.steps(message)[0]["content"] == '{"reason": "The plan’s limit"}'
