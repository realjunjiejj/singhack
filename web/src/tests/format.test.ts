import { describe, expect, it } from "vitest";
import { formatMeasure, formatMoney } from "@/lib/workbench/format";

describe("financial presentation formatting", () => {
  it("keeps the ISO currency visible", () => {
    expect(formatMoney({ amount: 8_000_000, currency: "SGD" })).toMatch(/^SGD\s?8,000,000$/);
  });

  it("formats supplied percentage measures without recalculating them", () => {
    expect(formatMeasure({ value: 59.15, unit: "percent" })).toBe("59.15%");
  });
});
