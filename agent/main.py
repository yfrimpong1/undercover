"""The UnderCover Agent."""

import json
import os
from collections.abc import Iterator
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://localhost:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"
MAX_GRAPH_STEPS = 50


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


def get(path: str) -> str:
    """Read from the backend and return its reply, errors included."""
    with backend() as client:
        return client.get(path).text


def post(path: str, body: dict[str, Any]) -> str:
    """Send to the backend and return its reply, errors included."""
    with backend() as client:
        return client.post(path, json=body).text


@tool
def get_claim(claim_id: str) -> str:
    """Read a claim: the customer's story, the items claimed and the documents."""
    return get(f"/api/claims/{claim_id}")


@tool
def get_policy(policy_id: str) -> str:
    """Read the policy named on the claim, with its plan's limits and deductible."""
    return get(f"/api/policies/{policy_id}")


@tool
def get_claim_history(customer_id: str) -> str:
    """Read the earlier claims of the customer named on the claim."""
    return get(f"/api/customers/{customer_id}/claim-history")


@tool
def get_policy_wording() -> str:
    """Read the policy wording: what each benefit covers and how payouts work."""
    return get("/api/policy-wording")


def claim_tools(claim_id: str) -> list[BaseTool]:
    """Return the agent's tools, with deciding and paying tied to one claim."""

    @tool
    def decide_claim(
        decision: Literal["approve", "decline", "refer"],
        payout: float,
        reason: str,
        policy_section: int,
    ) -> str:
        """Record your decision on the claim.

        Give the payout in US dollars ($0.00 unless you approve), the reason in
        two or three plain sentences, and the number of the section of the
        policy wording that the decision rests on.
        """
        return post(
            f"/api/claims/{claim_id}/decision",
            {
                "decision": decision,
                "payout": payout,
                "reason": reason,
                "policy_section": policy_section,
            },
        )

    @tool
    def pay_claim(amount: float) -> str:
        """Pay the approved payout on the claim, in US dollars."""
        return post(f"/api/claims/{claim_id}/payment", {"amount": amount})

    return [
        get_claim,
        get_policy,
        get_claim_history,
        get_policy_wording,
        decide_claim,
        pay_claim,
    ]


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def steps(message: BaseMessage) -> list[dict[str, str]]:
    """Turn one of the agent's messages into the steps the dashboard shows."""
    if isinstance(message, ToolMessage):
        return [
            {"kind": "tool_result", "name": str(message.name), "content": message.text}
        ]
    found = []
    if message.text:
        found.append({"kind": "message", "name": "agent", "content": message.text})
    if isinstance(message, AIMessage):
        found += [
            {
                "kind": "tool_call",
                "name": call["name"],
                "content": json.dumps(call["args"]),
            }
            for call in message.tool_calls
        ]
    return found


def messages(
    claim_id: str, thread_id: str, instructions: str, llm: BaseChatModel
) -> Iterator[BaseMessage]:
    """Run the agent on a claim and yield each new message as it arrives."""
    agent = create_agent(llm, tools=claim_tools(claim_id), system_prompt=instructions)
    for update in agent.stream(
        {"messages": [{"role": "user", "content": f"Please decide claim {claim_id}."}]},
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": MAX_GRAPH_STEPS,
        },
        stream_mode="updates",
    ):
        for node in update.values():
            yield from node["messages"]


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Work one claim, recording each step, and return the agent's final reply."""
    reply = ""
    with backend() as client:
        client.post(f"/api/claims/{claim_id}/start").raise_for_status()
        instructions = client.get("/api/instructions").raise_for_status().json()
        for message in messages(
            claim_id, thread_id, instructions["text"], llm or model()
        ):
            for step in steps(message):
                client.post(
                    f"/api/claims/{claim_id}/steps", json=step
                ).raise_for_status()
            reply = message.text
    return reply
