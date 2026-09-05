import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { getExecutiveInsight } from "@/lib/intelligence/executiveAnalysis";
import { analysisErrorMessage, intelligenceMatchesWorkbench } from "@/lib/intelligence/source";
import type { IntelligenceRun } from "@/lib/intelligence/types";
import type { WorkbenchModel } from "@/lib/workbench/types";
import { createInitialState } from "@/lib/state/model";
import { workbenchReducer } from "@/lib/state/reducer";

const model: WorkbenchModel = JSON.parse(readFileSync(path.resolve(process.cwd(), "../artifacts/workbench.json"), "utf8"));
const run: IntelligenceRun = { schemaVersion: "1.0.0", runId: "test", generatedAt: "test", status: "completed", deepFocus: [], diagnostics: [], agentReports: [], workbench: model };

describe("demo and upload evidence integrity", () => {
  it("derives every executive story from the loaded case, including reused demo IDs", () => {
    for (const original of model.clientCases) {
      const clientCase = structuredClone(original);
      clientCase.conclusion = "New uploaded conclusion";
      clientCase.meetingBrief.whatChanged = "New uploaded facts";
      clientCase.meetingBrief.whyItMatters = "New client objective";
      clientCase.meetingBrief.openingQuestion = "New opening question?";
      clientCase.meetingBrief.discussionOptions = ["Confirm the new obligation"];
      const insight = getExecutiveInsight(clientCase);
      expect(insight.headline).toBe(clientCase.conclusion);
      expect(insight.whatHappened.summary).toBe("New uploaded facts");
      expect(insight.clientDilemma.tension).toBe("New client objective");
      expect(insight.conversationScript.opener).toBe("New opening question?");
      expect(insight.whatShouldBeDone.map((item) => item.detail)).toEqual(clientCase.meetingBrief.discussionOptions);
    }
  });

  it("rejects stale intelligence even when the same client IDs and date are reused", () => {
    expect(intelligenceMatchesWorkbench(run, model)).toBe(true);
    const changed = structuredClone(model);
    changed.clientCases[0].conclusion = "Changed source";
    expect(intelligenceMatchesWorkbench(run, changed)).toBe(false);
    expect(intelligenceMatchesWorkbench(null, model)).toBe(false);
    expect(intelligenceMatchesWorkbench({ ...run, workbench: undefined }, model)).toBe(false);
    const reordered = { evidencePackets: model.evidencePackets, clientCases: model.clientCases, book: model.book, meta: model.meta };
    expect(intelligenceMatchesWorkbench(run, reordered)).toBe(true);
  });

  it("clears old approvals, resolutions, notes and filters on source adoption", () => {
    const clientCase = model.clientCases[0];
    let state = workbenchReducer(createInitialState(), { type: "SOURCE_READY", artifactKind: "generated", schemaVersion: "1.0.0" });
    state = workbenchReducer(state, { type: "SELECT_CASE", caseId: clientCase.caseId, snapshots: ["old", "old"] });
    state = workbenchReducer(state, { type: "PREPARE_BRIEF", caseId: clientCase.caseId, seed: clientCase.meetingBrief });
    state = workbenchReducer(state, { type: "APPROVE_BRIEF", caseId: clientCase.caseId });
    state = workbenchReducer(state, { type: "SET_CASE_RESOLUTION", caseId: clientCase.caseId, resolution: "conversation-prepared" });
    state = workbenchReducer(state, { type: "SET_OPEN_LOOP_STATE", openLoopId: "old", state: "confirmed" });
    state = workbenchReducer(state, { type: "SET_FILTERS", filters: { query: "old" } });
    state = workbenchReducer(state, { type: "SOURCE_READY", artifactKind: "generated", schemaVersion: "1.0.0" });
    expect(state).toEqual({ ...createInitialState(), source: { status: "ready", artifactKind: "generated", schemaVersion: "1.0.0" } });
  });

  it("shows actionable engine diagnostics rather than a generic 422", () => {
    expect(analysisErrorMessage({ diagnostics: [{ message: "Missing holdings.csv" }] }, 422)).toBe("Missing holdings.csv");
    expect(analysisErrorMessage({ detail: "Engine unavailable" }, 503)).toBe("Engine unavailable");
    expect(analysisErrorMessage(null, 500)).toContain("500");
  });
});
