import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ClientReadyView } from "@/components/work-surface/ClientReadyView";
import type { ClientCase } from "@/lib/workbench/types";

const clientCase: ClientCase = {
  caseId: "CASE-CL-0003", clientId: "CL-0003", clientName: "Margarethe Voss-Brenner", reportingLanguage: "German",
  conclusion: "A suitability mismatch needs review.", whyNow: "EUR 3.4m is due.", status: "active",
  urgency: { tier: "Critical", score: 100, safetyOverride: { ruleId: "cash", reason: "Need due" } },
  confidence: { level: "Low", score: 48, reasons: ["USD 22.18m and USD 20.31m conflict"] },
  facts: [], interpretations: [], uncertainties: [], factorContributions: [], anticipatorySignals: [], openLoops: [], governanceClocks: [], timeline: [],
  evidencePacketIds: ["PACKET-M"], allowedGuidedActions: ["show-evidence", "prepare-conversation"],
  meetingBrief: { whatChanged: "EUR 3.4m is due.", whyItMatters: "USD 22.18m and USD 20.31m disagree.", uncertainties: [], openingQuestion: "May we review this?", discussionOptions: [], specialistSuggestion: null, openLoopIds: [], governanceClockIds: [], evidenceItemIds: ["E-M-TAX", "E-M-CONFLICT"] },
  clientReadyDrafts: [
    { language: "English", canonicalLanguage: "English", status: "draft", content: "EUR 3.4m · USD 22.18m · USD 20.31m · E-M-TAX · E-M-CONFLICT", evidenceItemIds: ["E-M-TAX", "E-M-CONFLICT"] },
    { language: "German", canonicalLanguage: "English", status: "draft", content: "EUR 3.4m · USD 22.18m · USD 20.31m · E-M-TAX · E-M-CONFLICT", evidenceItemIds: ["E-M-TAX", "E-M-CONFLICT"] },
  ],
};

describe("Client-Ready View", () => {
  it("renders canonical and reporting-language payloads with unchanged financial tokens and citations", () => {
    const { container } = render(<ClientReadyView clientCase={clientCase} onEvidence={vi.fn()} />);
    expect(screen.getByText("Client reporting language · German")).toBeInTheDocument();
    for (const token of ["EUR 3.4m", "USD 22.18m", "USD 20.31m", "E-M-TAX", "E-M-CONFLICT"]) {
      expect(container.textContent?.split(token).length).toBeGreaterThanOrEqual(3);
    }
    expect(screen.getAllByRole("button", { name: "Open evidence E-M-TAX" })).toHaveLength(2);
  });
});
