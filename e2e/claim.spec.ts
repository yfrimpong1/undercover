import { expect, test } from "@playwright/test";
import { decide } from "./api";

test("the claim page shows a claim in full", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "CLM-1001" }).click();
  await expect(page).toHaveURL("/claims/CLM-1001");
  await expect(page.getByText(/^My flight home from Rome/)).toBeVisible();
  await expect(page.locator(".items tbody tr")).toHaveCount(3);
  await expect(page.locator(".document")).toHaveCount(4);
  await expect(page.getByText("UnderCover Premium")).toBeVisible();
  await expect(page.getByText("CLM-0412")).toBeVisible();
  await expect(
    page.getByText("The agent hasn't decided this claim yet."),
  ).toBeVisible();
});

test("steps recorded through the API appear without a reload", async ({
  page,
  request,
}) => {
  await page.goto("/claims/CLM-1002");
  await expect(
    page.getByText("Suitcase lost on a connecting flight"),
  ).toBeVisible();
  await page.evaluate(() => {
    document.body.dataset.loaded = "once";
  });
  await request.post("/api/claims/CLM-1002/start");
  await request.post("/api/claims/CLM-1002/steps", {
    data: { kind: "message", name: "agent", content: "Reading the claim now." },
  });
  await expect(page.getByText("Reading the claim now.")).toBeVisible();
  await expect(page.locator("body")).toHaveAttribute("data-loaded", "once");
});

test("a payment over $1,000.00 waits for a sign-off", async ({
  page,
  request,
}) => {
  await decide(request, "CLM-1003", {
    decision: "approve",
    payout: 1500,
    policy_section: 7,
  });
  const payment = await request.post("/api/claims/CLM-1003/payment", {
    data: { amount: 1500 },
  });
  expect(payment.status()).toBe(403);
  expect(await payment.json()).toEqual({
    detail: "A payout over $1,000.00 needs a handler's sign-off",
  });
  await page.goto("/claims/CLM-1003");
  await expect(
    page.getByText("Waiting for a handler's sign-off"),
  ).toBeVisible();
  await expect(page.getByText(/^Paid /)).toHaveCount(0);
});

test("a handler signs off a payout and it's paid", async ({
  page,
  request,
}) => {
  await decide(request, "CLM-1008", {
    decision: "approve",
    payout: 2000,
    policy_section: 2,
  });
  await page.goto("/claims/CLM-1008");
  await page.getByLabel("Handler").selectOption({ label: "Priya Raman" });
  await page
    .getByRole("button", { name: "Sign off and pay $2,000.00" })
    .click();
  await expect(
    page.getByText(/^Paid \$2,000\.00, signed off by Priya Raman on /),
  ).toBeVisible();
  await expect(page.locator(".claim-title .badge")).toHaveText("Decided");
});
