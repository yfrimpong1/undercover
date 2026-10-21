import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { InstructionsPage } from "./InstructionsPage";
import { mockApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the agent's instructions, read only", async () => {
  mockApi({ "/instructions": { text: "You are the UnderCover Agent." } });
  const { container } = render(<InstructionsPage />);
  expect(
    await screen.findByText("You are the UnderCover Agent."),
  ).toBeDefined();
  expect(
    container.querySelector("textarea, input, [contenteditable]"),
  ).toBeNull();
});

it("says when the backend isn't reachable", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
  render(<InstructionsPage />);
  expect(await screen.findByRole("alert")).toBeDefined();
});
