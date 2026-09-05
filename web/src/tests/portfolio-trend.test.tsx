import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PortfolioTrend } from "@/components/case/PortfolioTrend";
import type { TimelinePoint } from "@/lib/workbench/types";

const timeline: TimelinePoint[] = [
  { date: "2025-12-31", label: "Trigger breached", metrics: { ltv: { value: 78.5, unit: "percent" } }, evidenceItemIds: ["E-OLD"] },
  { date: "2026-08-26", label: "Current safe status", metrics: { ltv: { value: 59.15, unit: "percent" } }, evidenceItemIds: ["E-NOW"] },
];

describe("Portfolio trend", () => {
  it("visualises supplied position values and exposes the same values accessibly", () => {
    render(<PortfolioTrend timeline={timeline} metric="ltv" trigger={70} onEvidence={vi.fn()} />);
    expect(screen.getByRole("img", { name: /LTV trend.*78.50%.*59.15%/i })).toBeInTheDocument();
    expect(screen.getByText("70% trigger")).toBeInTheDocument();
    expect(screen.getByText("Current safe status")).toBeInTheDocument();
  });
});
