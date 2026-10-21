import type { APIRequestContext } from "@playwright/test";

/** Start a claim and record a decision on it, as the agent would. */
export async function decide(
  request: APIRequestContext,
  claimId: string,
  decision: { decision: string; payout: number; policy_section: number },
) {
  await request.post(`/api/claims/${claimId}/start`);
  return request.post(`/api/claims/${claimId}/decision`, {
    data: { ...decision, reason: "Set up by an end-to-end test." },
  });
}
