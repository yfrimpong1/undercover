import { expect, test } from "@playwright/test";

test("the queue lists the claims with their statuses", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(25);
  const row = page.getByTestId("row-CLM-1025");
  await expect(row.getByText("Waiting", { exact: true })).toBeVisible();
  await expect(row.getByRole("link", { name: "CLM-1025" })).toHaveAttribute(
    "href",
    "/claims/CLM-1025",
  );
});

test("the instructions page shows the instructions, read only", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Agent instructions" }).click();
  await expect(page.getByText(/^You are the UnderCover Agent/)).toBeVisible();
  await expect(page.locator("textarea, input, [contenteditable]")).toHaveCount(
    0,
  );
});
