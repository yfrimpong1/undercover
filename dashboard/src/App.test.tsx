import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { claim, claimRoutes, mockApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the queue at /", async () => {
  mockApi({ "/claims": [] });
  render(<App path="/" />);
  expect(
    await screen.findByRole("heading", { name: "Claims queue" }),
  ).toBeDefined();
  expect(
    screen.getByRole("link", { name: "Claims" }).getAttribute("aria-current"),
  ).toBe("page");
});

it("shows the instructions at /instructions", async () => {
  mockApi({ "/instructions": { text: "Decide claims." } });
  render(<App path="/instructions" />);
  expect(
    await screen.findByRole("heading", { name: "Agent instructions" }),
  ).toBeDefined();
  expect(
    screen
      .getByRole("link", { name: "Agent instructions" })
      .getAttribute("aria-current"),
  ).toBe("page");
});

it("shows a claim at /claims/<id>", async () => {
  mockApi(claimRoutes(claim()));
  render(<App path="/claims/CLM-1001" />);
  expect(
    await screen.findByText("Flight home canceled by the airline"),
  ).toBeDefined();
});
