import { vi } from "vitest";
import type { ClaimSummary } from "./api";

/** Stand in for the backend: answer each API path with its JSON, else 404. */
export function mockApi(routes: Record<string, unknown>) {
  const fetchMock = vi.fn((input: string, init?: RequestInit) => {
    const path = input.replace(/^\/api/, "");
    const key = init?.method === "POST" ? `POST ${path}` : path;
    if (key in routes) return Promise.resolve(Response.json(routes[key]));
    return Promise.resolve(
      Response.json({ detail: `${key} not found` }, { status: 404 }),
    );
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function summary(overrides: Partial<ClaimSummary> = {}): ClaimSummary {
  return {
    claim_id: "CLM-1001",
    customer_name: "Maya Patel",
    claim_type: "trip_delay",
    summary: "Flight home canceled",
    submitted_on: "2026-06-24",
    amount_claimed: 420,
    status: "waiting",
    decision: null,
    payout: null,
    paid: false,
    ...overrides,
  };
}
