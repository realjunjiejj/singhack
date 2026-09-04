import { describe, expect, it } from "vitest";
import { filterPriorityQueue } from "@/lib/state/selectors";
import type { PriorityQueueItem } from "@/lib/workbench/types";

const row = (rank: number, name: string, tier: "Critical" | "High" | "Watch"): PriorityQueueItem => ({
  rank,
  caseId: `CASE-${rank}`,
  clientId: `CL-${rank}`,
  clientName: name,
  bookingCentre: rank === 1 ? "Singapore" : "Hong Kong",
  reportingLanguage: "English",
  urgency: { tier, score: 90 - rank, safetyOverride: null },
  confidence: { level: rank === 1 ? "High" : "Low", score: 80, reasons: [] },
  priorityRationale: `${name} rationale`,
  factorContributions: [],
  status: "normal",
  signalSummaries: [rank === 1 ? "credit" : "liquidity"],
  openLoopCount: 0,
  governanceClockCount: 0,
});

describe("Priority Queue filtering", () => {
  it("only hides rows and preserves artifact order", () => {
    const rows = [row(1, "First", "High"), row(2, "Second", "Watch"), row(3, "Third", "High")];
    const result = filterPriorityQueue(rows, {
      query: "",
      signalTypes: [],
      bookingCentres: [],
      urgencyTiers: ["High"],
      confidenceLevels: [],
    });
    expect(result.map((item) => item.rank)).toEqual([1, 3]);
  });

  it("preserves all 20 artifact ranks without sorting", () => {
    const rows = Array.from({ length: 20 }, (_, index) => row(index + 1, `Client ${index + 1}`, index < 4 ? "Critical" : index < 12 ? "High" : "Watch"));
    const result = filterPriorityQueue(rows, {
      query: "",
      signalTypes: [],
      bookingCentres: [],
      urgencyTiers: [],
      confidenceLevels: [],
    });
    expect(result.map((item) => item.rank)).toEqual(Array.from({ length: 20 }, (_, index) => index + 1));
  });

  it("uses artifact-provided Anticipatory Signal types for signal filtering", () => {
    const rows = [row(1, "Credit Client", "High"), row(2, "Liquidity Client", "Watch")];
    const result = filterPriorityQueue(rows, {
      query: "",
      signalTypes: ["cash-need"],
      bookingCentres: [],
      urgencyTiers: [],
      confidenceLevels: [],
    }, [{ caseId: "CASE-2", anticipatorySignals: [{ type: "cash-need" }] } as never]);
    expect(result.map((item) => item.rank)).toEqual([2]);
  });
});
