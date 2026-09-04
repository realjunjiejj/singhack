import type { CaseStatus, Measure, Money } from "./types";

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(
    new Date(`${value}T00:00:00Z`),
  );
}

export function formatMoney(value: Money) {
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: value.currency,
    currencyDisplay: "code",
    maximumFractionDigits: value.amount >= 1_000_000 ? 0 : 2,
  }).format(value.amount);
}

export function formatMeasure(value: Measure) {
  if (value.unit === "percent") return `${value.value.toFixed(2)}%`;
  if (value.currency) return formatMoney({ amount: value.value, currency: value.currency });
  return `${new Intl.NumberFormat("en-SG", { maximumFractionDigits: 4 }).format(value.value)} ${value.unit}`;
}

export function formatEvidenceValue(value: unknown): string {
  if (value === null || value === undefined) return "Not supplied";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  if (typeof value === "object" && "amount" in value && "currency" in value) return formatMoney(value as Money);
  return Object.entries(value as Record<string, unknown>)
    .map(([key, item]) => `${key.replace(/([A-Z])/g, " $1")}: ${formatEvidenceValue(item)}`)
    .join(" · ");
}

export const statusLabels: Record<CaseStatus, string> = {
  active: "Active",
  near: "Near trigger",
  "historical-resolved": "Historical — resolved",
  normal: "Current — normal",
};

export function sentenceCase(value: string) {
  const spaced = value.replace(/-/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
