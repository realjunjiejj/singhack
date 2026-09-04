import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ClientReadyView } from "@/components/work-surface/ClientReadyView";
import type { MeetingBriefState } from "@/lib/state/model";
import type { ClientCase } from "@/lib/workbench/types";

const clientCase: ClientCase = {
  caseId: "CASE-CL-0003", clientId: "CL-0003", clientName: "Margarethe Voss-Brenner", reportingLanguage: "German",
  conclusion: "A suitability mismatch needs review.", whyNow: "EUR 3.4m is due.", status: "active",
  urgency: { tier: "Critical", score: 100, safetyOverride: { ruleId: "cash", reason: "Need due" } },
  confidence: { level: "High", score: 92, reasons: ["Portfolio totals reconcile after FX conversion"] },
  facts: [], interpretations: [], uncertainties: [], factorContributions: [], anticipatorySignals: [], openLoops: [], governanceClocks: [], timeline: [],
  evidencePacketIds: ["PACKET-M"], allowedGuidedActions: ["show-evidence", "prepare-conversation"],
  meetingBrief: { whatChanged: "EUR 3.4m is due.", whyItMatters: "USD 22.18m is reconciled after FX conversion.", uncertainties: [], openingQuestion: "May we review this?", discussionOptions: [], specialistSuggestion: null, openLoopIds: [], governanceClockIds: [], evidenceItemIds: ["E-M-TAX", "E-M-FX"] },
  clientReadyDrafts: [
    { language: "English", canonicalLanguage: "English", status: "draft", content: "EUR 3.4m · USD 22.18m · E-M-TAX · E-M-FX", evidenceItemIds: ["E-M-TAX", "E-M-FX"] },
    { language: "German", canonicalLanguage: "English", status: "draft", content: "EUR 3.4m · USD 22.18m · E-M-TAX · E-M-FX", evidenceItemIds: ["E-M-TAX", "E-M-FX"] },
  ],
};

describe("Client-Ready View", () => {
  it("renders canonical and reporting-language payloads with unchanged financial tokens and citations", () => {
    const { container } = render(<ClientReadyView clientCase={clientCase} onEvidence={vi.fn()} />);
    expect(screen.getByText("Client reporting language · German")).toBeInTheDocument();
    for (const token of ["EUR 3.4m", "USD 22.18m"]) {
      expect(container.textContent?.split(token).length).toBeGreaterThanOrEqual(3);
    }
    expect(screen.getAllByRole("button", { name: "Open evidence E-M-TAX" })).toHaveLength(2);
  });

  it("shows approved RM edits only in canonical copy and marks translation stale", () => {
    const brief: MeetingBriefState = {
      revision: 2,
      status: "approved",
      approvedRevision: 2,
      edited: true,
      sourceFields: clientCase.meetingBrief,
      fields: {
        ...clientCase.meetingBrief,
        whatChanged: "RM-confirmed tax funding discussion.",
      },
    };

    render(
      <ClientReadyView
        clientCase={clientCase}
        brief={brief}
        onEvidence={vi.fn()}
      />,
    );

    expect(screen.getByText(/RM-confirmed tax funding discussion/)).toBeInTheDocument();
    expect(screen.getByText("RM-approved revision 2")).toBeInTheDocument();
    expect(screen.getByText("Cached draft · refresh after RM edits")).toBeInTheDocument();
    expect(screen.getByText(/RM edits update the canonical view only/)).toBeInTheDocument();
  });
});
