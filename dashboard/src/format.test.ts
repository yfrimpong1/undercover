import { expect, it } from "vitest";
import { date, dayOf, label, money, time } from "./format";

it("writes money in US dollars", () => {
  expect(money(1250)).toBe("$1,250.00");
  expect(money(420)).toBe("$420.00");
});

it("writes a calendar date without shifting the day", () => {
  expect(date("2026-06-24")).toBe("Jun 24, 2026");
});

it("writes the day and time of a moment", () => {
  expect(dayOf("2026-10-21T12:00:00+00:00")).toMatch(/^Oct 2\d, 2026$/);
  expect(time("2026-10-21T12:00:00+00:00")).toMatch(/^\d{1,2}:00:00\s[AP]M$/);
});

it("turns codes into labels", () => {
  expect(label("trip_delay")).toBe("Trip delay");
  expect(label("emergency_medical")).toBe("Emergency medical");
  expect(label("passport")).toBe("Passport");
});
