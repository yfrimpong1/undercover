import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { POLL_MS, usePolling } from "./usePolling";

function Counter({ load }: Readonly<{ load: () => Promise<number> }>) {
  const { data, error, refresh } = usePolling(load);
  return (
    <>
      <p>{error ? `Error: ${error.message}` : `Count: ${String(data)}`}</p>
      <button onClick={refresh}>Refresh</button>
    </>
  );
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

async function flush(ms = 0) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

it("loads at once and again every two seconds", async () => {
  let count = 0;
  const load = vi.fn(() => Promise.resolve(++count));
  render(<Counter load={load} />);
  await flush();
  expect(screen.getByText("Count: 1")).toBeDefined();
  await flush(POLL_MS);
  expect(screen.getByText("Count: 2")).toBeDefined();
});

it("keeps an error until a load succeeds", async () => {
  const load = vi
    .fn<() => Promise<number>>()
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValue(7);
  render(<Counter load={load} />);
  await flush();
  expect(screen.getByText("Error: offline")).toBeDefined();
  await flush(POLL_MS);
  expect(screen.getByText("Count: 7")).toBeDefined();
});

it("loads again on request", async () => {
  let count = 0;
  const load = vi.fn(() => Promise.resolve(++count));
  render(<Counter load={load} />);
  await flush();
  act(() => {
    screen.getByRole("button", { name: "Refresh" }).click();
  });
  await flush();
  expect(screen.getByText("Count: 2")).toBeDefined();
});

it("stops loading when it goes away", async () => {
  const load = vi.fn(() => Promise.resolve(1));
  const { unmount } = render(<Counter load={load} />);
  await flush();
  unmount();
  await flush(POLL_MS * 2);
  expect(load).toHaveBeenCalledTimes(1);
});
