import { vi } from "vitest";
import type {
  Claim,
  ClaimSummary,
  Customer,
  Decision,
  Handler,
  Policy,
  Step,
} from "./api";

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

export function claim(overrides: Partial<Claim> = {}): Claim {
  return {
    claim_id: "CLM-1001",
    policy_id: "POL-2001",
    customer_id: "CUS-3001",
    customer_name: "Maya Patel",
    claim_type: "trip_delay",
    submitted_on: "2026-06-24",
    incident_date: "2026-06-18",
    incident_location: "Rome, Italy",
    summary: "Flight home canceled by the airline",
    story: "My flight home from Rome was canceled.",
    items: [
      {
        description: "Airport hotel, one night",
        category: "accommodation",
        amount: 245,
      },
      { description: "Dinner and breakfast", category: "meals", amount: 95 },
      { description: "Taxis", category: "transport", amount: 80 },
    ],
    amount_claimed: 420,
    documents: [
      {
        name: "Cancellation notice",
        type: "carrier_report",
        content: "Flight MA 611 was canceled.",
      },
      {
        name: "Hotel receipt",
        type: "receipt",
        content: "One night: $245.00.",
      },
    ],
    status: "waiting",
    started_at: null,
    decision: null,
    payment: null,
    sign_off: null,
    ...overrides,
  };
}

export function decision(overrides: Partial<Decision> = {}): Decision {
  return {
    decision: "approve",
    payout: 420,
    reason: "The delay is covered.",
    policy_section: 3,
    policy_section_title: "3. Trip Delay",
    policy_section_text: "We pay when your carrier delays you.",
    decided_at: "2026-10-21T12:00:00+00:00",
    ...overrides,
  };
}

export const policy: Policy = {
  policy_id: "POL-2001",
  customer_id: "CUS-3001",
  plan: {
    plan: "premium",
    name: "UnderCover Premium",
    trip_cancellation_max: 5000,
    trip_delay_waiting_hours: 6,
    trip_delay_max: 800,
    baggage_delay_waiting_hours: 12,
    baggage_delay_max: 300,
    baggage_max: 1500,
    per_item_limit: 300,
    passport_max: 250,
    emergency_medical_max: 100000,
    deductible: 50,
  },
  add_ons: [],
  purchased_on: "2026-04-22",
  sold_through: "Meridian Air checkout",
  trip: {
    destination: "Rome, Italy",
    departs_on: "2026-06-10",
    returns_on: "2026-06-18",
    trip_cost: 3100,
  },
  travelers: ["Maya Patel"],
  status: "active",
};

export const customer: Customer = {
  customer_id: "CUS-3001",
  name: "Maya Patel",
  email: "maya.patel@example.com",
  phone: "+1 201 555 0143",
  date_of_birth: "1988-03-14",
  address: {
    street: "48 Wayne Street",
    city: "Jersey City",
    state: "NJ",
    zip: "07302",
  },
  customer_since: "2023-04-11",
  previous_claims: [
    {
      claim_id: "CLM-0412",
      filed_on: "2024-08-19",
      incident_date: "2024-08-09",
      claim_type: "baggage_delay",
      summary: "Checked bag arrived 30 hours late in Lisbon",
      outcome: "approved",
      amount_paid: 140,
    },
  ],
};

export const handlers: Handler[] = [
  {
    handler_id: "HND-01",
    name: "Dana Whitfield",
    role: "Senior Claims Handler",
    email: "dana@undercover.example",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-02",
    name: "Marcus Oyelaran",
    role: "Claims Handler",
    email: "marcus@undercover.example",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-09",
    name: "Sam Trainee",
    role: "Trainee",
    email: "sam@undercover.example",
    can_approve_over_limit: false,
  },
];

/** The routes the claim page reads, for one claim and its steps. */
export function claimRoutes(theClaim: Claim, steps: Step[] = []) {
  return {
    [`/claims/${theClaim.claim_id}`]: theClaim,
    [`/claims/${theClaim.claim_id}/steps`]: steps,
    "/handlers": handlers,
    "/policies/POL-2001": policy,
    "/customers/CUS-3001": customer,
  } as Record<string, unknown>;
}
