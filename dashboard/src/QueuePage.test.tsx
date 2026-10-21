import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueuePage } from "./QueuePage";
import { mockApi, summary } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const claims = [
  summary(),
  summary({ claim_id: "CLM-1002", status: "in_progress" }),
  summary({
    claim_id: "CLM-1003",
    status: "waiting_for_sign_off",
    decision: "approve",
    payout: 3750,
  }),
  summary({
    claim_id: "CLM-1004",
    status: "decided",
    decision: "approve",
    payout: 186,
    paid: true,
  }),
  summary({
    claim_id: "CLM-1005",
    status: "decided",
    decision: "decline",
    payout: 0,
  }),
];

it("lists the claims with where each one stands", async () => {
  mockApi({ "/claims": claims });
  render(<QueuePage />);
  const row = await screen.findByTestId("row-CLM-1001");
  expect(
    within(row).getByRole("link", { name: "CLM-1001" }).getAttribute("href"),
  ).toBe("/claims/CLM-1001");
  expect(within(row).getByText("Maya Patel")).toBeDefined();
  expect(within(row).getByText("Trip delay")).toBeDefined();
  expect(within(row).getByText("Jun 24, 2026")).toBeDefined();
  expect(within(row).getByText("$420.00")).toBeDefined();
  expect(within(row).getByText("Waiting")).toBeDefined();
});

it("counts the claims in each status", async () => {
  mockApi({ "/claims": claims });
  render(<QueuePage />);
  expect((await screen.findByTestId("count-waiting")).textContent).toBe("1");
  expect(screen.getByTestId("count-in_progress").textContent).toBe("1");
  expect(screen.getByTestId("count-waiting_for_sign_off").textContent).toBe(
    "1",
  );
  expect(screen.getByTestId("count-decided").textContent).toBe("2");
});

it("shows decisions, payouts and payments", async () => {
  mockApi({ "/claims": claims });
  render(<QueuePage />);
  const waiting = await screen.findByTestId("row-CLM-1003");
  expect(within(waiting).getByText("Approve")).toBeDefined();
  expect(within(waiting).getByText("$3,750.00")).toBeDefined();
  expect(within(waiting).getByText("Not paid")).toBeDefined();
  expect(
    within(screen.getByTestId("row-CLM-1004")).getByText("Paid"),
  ).toBeDefined();
  const declined = screen.getByTestId("row-CLM-1005");
  expect(within(declined).getByText("Decline")).toBeDefined();
  expect(within(declined).queryByText("$0.00")).toBeNull();
});

it("says when the backend isn't reachable", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
  render(<QueuePage />);
  expect((await screen.findByRole("alert")).textContent).toBe(
    "The backend isn't reachable.",
  );
});
