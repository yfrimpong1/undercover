import { afterEach, expect, it, vi } from "vitest";
import { ApiError, getClaim, listClaims, signOffClaim } from "./api";
import { mockApi } from "./testing";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("reads JSON from the backend", async () => {
  mockApi({ "/claims": [] });
  expect(await listClaims()).toEqual([]);
});

it("raises the backend's detail as an error", async () => {
  mockApi({});
  const error = await getClaim("CLM-9999").catch((e: unknown) => e);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({
    status: 404,
    message: "/claims/CLM-9999 not found",
  });
});

it("raises an error for a reply that isn't JSON", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response("Bad gateway", { status: 502, statusText: "Bad Gateway" }),
      ),
  );
  await expect(listClaims()).rejects.toMatchObject({
    status: 502,
    message: "Bad Gateway",
  });
});

it("signs off a claim with the handler's id", async () => {
  const fetchMock = mockApi({ "POST /claims/CLM-1003/sign-off": {} });
  await signOffClaim("CLM-1003", "HND-01");
  expect(fetchMock).toHaveBeenCalledWith("/api/claims/CLM-1003/sign-off", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handler_id: "HND-01" }),
  });
});
