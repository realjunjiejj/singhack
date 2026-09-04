import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QueueItem } from "@/components/queue/QueueItem";
import type { PriorityQueueItem } from "@/lib/workbench/types";

const item: PriorityQueueItem = {
  rank: 7, caseId: "CASE-7", clientId: "CL-0007", clientName: "Keyboard Client", bookingCentre: "Singapore", reportingLanguage: "English",
  urgency: { tier: "Watch", score: 44, safetyOverride: null }, confidence: { level: "High", score: 92, reasons: [] },
  priorityRationale: "A visible and deterministic reason.", factorContributions: [], status: "normal", signalSummaries: ["mandate"], openLoopCount: 0, governanceClockCount: 0,
};

describe("Priority Queue item", () => {
  it("is selectable from the keyboard and keeps Confidence distinct from Urgency", async () => {
    const onSelect = vi.fn();
    render(<QueueItem item={item} active={false} onSelect={onSelect} />);
    await userEvent.tab();
    await userEvent.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledOnce();
    expect(screen.getByLabelText("Watch Urgency, score 44")).toBeInTheDocument();
    expect(screen.getByText("Confidence High · 92")).toBeInTheDocument();
  });
});
