import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Step } from "./api";
import { ClaimPage } from "./ClaimPage";
import { claim, claimRoutes, decision, mockApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function decisionPanel() {
  return screen.getByRole("region", { name: "The agent's decision" });
}

it("shows the claim in full", async () => {
  mockApi(claimRoutes(claim()));
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();
  const details = screen.getByRole("region", { name: "The claim" });
  expect(within(details).getByText("Airport hotel, one night")).toBeDefined();
  expect(within(details).getByText("$245.00")).toBeDefined();
  expect(within(details).getAllByText("$420.00")).toHaveLength(1);
  expect(
    within(details).getByText("Flight MA 611 was canceled."),
  ).toBeDefined();
  expect(within(details).getByText("Carrier report")).toBeDefined();
  const policy = screen.getByRole("region", { name: "Policy POL-2001" });
  expect(within(policy).getByText("UnderCover Premium")).toBeDefined();
  expect(
    within(policy).getByText("Rome, Italy, Jun 10, 2026 to Jun 18, 2026"),
  ).toBeDefined();
  expect(within(policy).getByText("$800.00 after 6 hours")).toBeDefined();
  expect(within(policy).getByText("None")).toBeDefined();
  const customer = screen.getByRole("region", { name: "Customer" });
  expect(within(customer).getByText("maya.patel@example.com")).toBeDefined();
  expect(within(customer).getByText("CLM-0412")).toBeDefined();
});

it("says when the agent hasn't decided yet", async () => {
  mockApi(claimRoutes(claim()));
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("The agent hasn't decided this claim yet."),
  ).toBeDefined();
  expect(
    screen.getByText("The agent hasn't started on this claim."),
  ).toBeDefined();
});

it("shows the decision, its section and the payment", async () => {
  mockApi(
    claimRoutes(
      claim({
        status: "decided",
        decision: decision(),
        payment: { amount: 420, paid_at: "2026-10-21T12:00:00+00:00" },
      }),
    ),
  );
  render(<ClaimPage claimId="CLM-1001" />);
  await screen.findByText("The delay is covered.");
  const panel = decisionPanel();
  expect(within(panel).getByText("Approve")).toBeDefined();
  expect(within(panel).getByText("3. Trip Delay")).toBeDefined();
  const wording = within(panel).getByText(
    "We pay when your carrier delays you.",
  );
  expect(wording.closest("details")?.open).toBe(false);
  expect(
    within(panel).getByText(/^Paid \$420\.00 on Oct 2\d, 2026$/),
  ).toBeDefined();
});

it("says when an approval isn't paid yet", async () => {
  mockApi(claimRoutes(claim({ status: "decided", decision: decision() })));
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("Not paid yet")).toBeDefined();
});

it("shows that a decline pays nothing", async () => {
  mockApi(
    claimRoutes(
      claim({
        status: "decided",
        decision: decision({ decision: "decline", payout: 0 }),
      }),
    ),
  );
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("No payment")).toBeDefined();
  expect(within(decisionPanel()).getByText("Decline")).toBeDefined();
});

const waiting = claim({
  status: "waiting_for_sign_off",
  decision: decision({ payout: 1500 }),
});

it("lets a handler sign off a payout over the limit", async () => {
  const routes = claimRoutes(waiting);
  routes["POST /claims/CLM-1001/sign-off"] = {};
  const fetchMock = mockApi(routes);
  render(<ClaimPage claimId="CLM-1001" />);
  const button = await screen.findByRole("button", {
    name: "Sign off and pay $1,500.00",
  });
  expect(screen.getByText("Waiting for a handler's sign-off")).toBeDefined();
  const select = screen.getByLabelText<HTMLSelectElement>("Handler");
  expect([...select.options].map((option) => option.text)).toEqual([
    "Dana Whitfield",
    "Marcus Oyelaran",
  ]);
  fireEvent.change(select, { target: { value: "HND-02" } });
  routes["/claims/CLM-1001"] = {
    ...waiting,
    status: "decided",
    payment: { amount: 1500, paid_at: "2026-10-21T12:00:00+00:00" },
    sign_off: {
      handler_id: "HND-02",
      handler_name: "Marcus Oyelaran",
      signed_off_at: "2026-10-21T12:00:00+00:00",
    },
  };
  fireEvent.click(button);
  expect(
    await screen.findByText(
      /^Paid \$1,500\.00, signed off by Marcus Oyelaran on Oct 2\d, 2026$/,
    ),
  ).toBeDefined();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/claims/CLM-1001/sign-off",
    expect.objectContaining({ body: JSON.stringify({ handler_id: "HND-02" }) }),
  );
  expect(screen.queryByRole("button", { name: /Sign off/ })).toBeNull();
});

it("shows why a sign-off failed", async () => {
  mockApi(claimRoutes(waiting));
  render(<ClaimPage claimId="CLM-1001" />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Sign off and pay $1,500.00" }),
  );
  expect((await screen.findByRole("alert")).textContent).toBe(
    "POST /claims/CLM-1001/sign-off not found",
  );
});

const steps: Step[] = [
  {
    step_id: 1,
    kind: "tool_call",
    name: "get_claim",
    content: '{"claim_id": "CLM-1001"}',
    created_at: "2026-10-21T12:00:00+00:00",
  },
  {
    step_id: 2,
    kind: "tool_call",
    name: "get_policy_wording",
    content: "{}",
    created_at: "2026-10-21T12:00:01+00:00",
  },
  {
    step_id: 3,
    kind: "tool_result",
    name: "get_claim",
    content: '{"claim_id":"CLM-1001"}',
    created_at: "2026-10-21T12:00:02+00:00",
  },
  {
    step_id: 4,
    kind: "tool_result",
    name: "pay_claim",
    content: "Internal Server Error",
    created_at: "2026-10-21T12:00:03+00:00",
  },
  {
    step_id: 5,
    kind: "message",
    name: "agent",
    content: "Approved and paid.",
    created_at: "2026-10-21T12:00:04+00:00",
  },
];

it("shows the agent's steps in order", async () => {
  mockApi(claimRoutes(claim({ status: "in_progress" }), steps));
  render(<ClaimPage claimId="CLM-1001" />);
  const panel = await screen.findByRole("region", {
    name: "The agent's steps",
  });
  const items = within(panel).getAllByRole("listitem");
  expect(items.map((item) => item.className)).toEqual([
    "step step-tool_call",
    "step step-tool_call",
    "step step-tool_result",
    "step step-tool_result",
    "step step-message",
  ]);
  expect(within(items[0]).getByText('{"claim_id": "CLM-1001"}')).toBeDefined();
  expect(items[1].querySelector(".args")).toBeNull();
  const result = within(items[2]).getByText(/"claim_id": "CLM-1001"/);
  expect(result.textContent).toBe('{\n  "claim_id": "CLM-1001"\n}');
  expect(result.closest("details")?.open).toBe(false);
  expect(within(items[3]).getByText("Internal Server Error")).toBeDefined();
  expect(within(items[4]).getByText("Approved and paid.")).toBeDefined();
});

it("says when a claim doesn't exist", async () => {
  mockApi({});
  render(<ClaimPage claimId="CLM-9999" />);
  expect(await screen.findByText("Claim CLM-9999 not found.")).toBeDefined();
});

it("says when the backend isn't reachable", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
  render(<ClaimPage claimId="CLM-1001" />);
  expect((await screen.findByRole("alert")).textContent).toBe(
    "The backend isn't reachable.",
  );
});
