import type { DecisionKind, Status } from "./api";

const dollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});
const day = { month: "short", day: "numeric", year: "numeric" } as const;
const calendarDay = new Intl.DateTimeFormat("en-US", {
  ...day,
  timeZone: "UTC",
});
const localDay = new Intl.DateTimeFormat("en-US", day);
const localTime = new Intl.DateTimeFormat("en-US", { timeStyle: "medium" });

export const STATUSES: Status[] = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "decided",
];

export const STATUS_LABELS: Record<Status, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  waiting_for_sign_off: "Waiting for sign-off",
  decided: "Decided",
};

export const DECISION_LABELS: Record<DecisionKind, string> = {
  approve: "Approve",
  decline: "Decline",
  refer: "Refer",
};

export function money(amount: number): string {
  return dollars.format(amount);
}

/** A calendar date, such as 2026-06-24, read without a time zone. */
export function date(isoDate: string): string {
  return calendarDay.format(new Date(isoDate));
}

/** The local day of a moment, such as 2026-10-21T03:51:14+00:00. */
export function dayOf(timestamp: string): string {
  return localDay.format(new Date(timestamp));
}

export function time(timestamp: string): string {
  return localTime.format(new Date(timestamp));
}

export function label(code: string): string {
  const text = code.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
