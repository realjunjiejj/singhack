import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PriorityQueue } from "@/components/queue/PriorityQueue";
import { selectFeaturedCases } from "@/lib/workbench/featuredCases";
import type { PriorityQueueItem, WorkbenchModel } from "@/lib/workbench/types";
import type { WorkbenchState } from "@/lib/state/model";

function queueItem(
  clientId: string,
  clientName: string,
  rank: number,
): PriorityQueueItem {
  return {
    rank,
    caseId: `CASE-${clientId}`,
    clientId,
    clientName,
    bookingCentre: "Zurich",
    reportingLanguage: "English",
    urgency: { tier: "Watch", score: 40 - rank, safetyOverride: null },
    confidence: { level: "High", score: 90, reasons: [] },
    priorityRationale: "A visible and deterministic reason for this position.",
    factorContributions: [],
    status: "normal",
    signalSummaries: [],
    openLoopCount: 0,
    governanceClockCount: 0,
  };
}

const SINGHACKS_QUEUE = [
  queueItem("CL-0005", "Aishah binti Rahman", 1),
  queueItem("CL-0003", "Margarethe Voss-Brenner", 2),
  queueItem("CL-0001", "Hartono Wijaya Kusuma", 3),
  queueItem("CL-0012", "Cheung Kwok Wing", 4),
];

const SECOND_BOOK_QUEUE = [
  queueItem("MW-C-200", "Beatriz Alarcon", 1),
  queueItem("MW-C-100", "Anselm Roth", 2),
  queueItem("MW-C-400", "Dilnoza Karimova", 3),
  queueItem("MW-C-300", "Cyrus Danesh", 4),
];

function model(queue: PriorityQueueItem[]): WorkbenchModel {
  return {
    meta: {
      schemaVersion: "1.0.0",
      artifactKind: "generated",
      asOfDate: "2026-03-31",
      generatedAt: "2026-04-01T00:00:00Z",
      sourceSnapshotDates: ["2025-06-30", "2026-03-31"],
      dataQuality: { status: "clear", issues: [] },
    },
    book: {
      rm: { id: "RM-ZH-401", name: "Ingrid Solberg" },
      clientCount: queue.length,
      portfolioCount: queue.length,
      summary: { critical: 0, high: 0, watch: queue.length },
      filters: {
        signalTypes: [],
        bookingCentres: ["Zurich"],
        urgencyTiers: ["Critical", "High", "Watch"],
        confidenceLevels: ["High", "Medium", "Low"],
      },
      priorityQueue: queue,
    },
    clientCases: [],
    evidencePackets: [],
  } as unknown as WorkbenchModel;
}

const state = {
  activeCaseId: null,
  filters: {
    query: "",
    signalTypes: [],
    bookingCentres: [],
    urgencyTiers: [],
    confidenceLevels: [],
  },
} as unknown as WorkbenchState;

function renderQueue(queue: PriorityQueueItem[], onSelect = vi.fn()) {
  render(
    <PriorityQueue
      model={model(queue)}
      state={state}
      onFilters={vi.fn()}
      onSelect={onSelect}
      onEvidence={vi.fn()}
    />,
  );
  return onSelect;
}

describe("selectFeaturedCases", () => {
  it("keeps the hackathon shortcuts and their order for the SingHacks Book", () => {
    const featured = selectFeaturedCases(SINGHACKS_QUEUE);
    expect(featured.isDemoBook).toBe(true);
    expect(featured.heading).toBe("Demo cases");
    expect(featured.cases.map((entry) => entry.label)).toEqual([
      "#1 Aishah",
      "Cheung",
    ]);
  });

  it("derives featured cases from queue order for any other Book", () => {
    const featured = selectFeaturedCases(SECOND_BOOK_QUEUE);
    expect(featured.isDemoBook).toBe(false);
    expect(featured.heading).toBe("Featured cases");
    expect(featured.cases.map((entry) => entry.clientId)).toEqual([
      "MW-C-200",
      "MW-C-100",
      "MW-C-400",
    ]);
    expect(featured.cases.map((entry) => entry.label)).toEqual([
      "Alarcon",
      "Roth",
      "Karimova",
    ]);
  });

  it("does not treat a partial demonstration Book as the demonstration Book", () => {
    const partial = SINGHACKS_QUEUE.filter((item) => item.clientId !== "CL-0012");
    const featured = selectFeaturedCases(partial);
    expect(featured.isDemoBook).toBe(false);
    expect(featured.cases.every((entry) => partial.some((i) => i.clientId === entry.clientId))).toBe(true);
  });

  it("never returns more shortcuts than a small Book contains", () => {
    const featured = selectFeaturedCases(SECOND_BOOK_QUEUE.slice(0, 2));
    expect(featured.cases).toHaveLength(2);
  });

  it("returns nothing for an empty queue", () => {
    expect(selectFeaturedCases([]).cases).toEqual([]);
  });
});

describe("Priority Queue shortcuts", () => {
  it("renders the demonstration shortcuts for the SingHacks Book", () => {
    renderQueue(SINGHACKS_QUEUE);
    expect(screen.getByRole("button", { name: "#1 Aishah", exact: true })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Cheung" })).toBeEnabled();
  });

  it("renders real featured cases for a Book with none of those clients", () => {
    renderQueue(SECOND_BOOK_QUEUE);
    expect(screen.getByLabelText("Featured cases")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Alarcon" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hartono" })).not.toBeInTheDocument();
  });

  it("never renders a disabled shortcut for an absent client", () => {
    renderQueue(SECOND_BOOK_QUEUE);
    for (const button of screen.getAllByRole("button")) {
      expect(button).not.toBeDisabled();
    }
  });

  it("selects the case the shortcut points at", async () => {
    const onSelect = renderQueue(SECOND_BOOK_QUEUE);
    await userEvent.click(screen.getByRole("button", { name: "Roth" }));
    expect(onSelect).toHaveBeenCalledWith("CASE-MW-C-100");
  });

  it("still renders the whole Priority Queue beneath the shortcuts", () => {
    renderQueue(SECOND_BOOK_QUEUE);
    expect(screen.getByText("4/4")).toBeInTheDocument();
  });
});
