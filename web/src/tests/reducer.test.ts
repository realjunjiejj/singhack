import { describe, expect, it } from "vitest";
import { createInitialState, type EditableBrief } from "@/lib/state/model";
import { workbenchReducer } from "@/lib/state/reducer";

const seed: EditableBrief = {
  whatChanged: "The facility returned below its trigger.",
  whyItMatters: "The buffer remains relevant.",
  uncertainties: ["Confirm the property timing."],
  openingQuestion: "How would you like to preserve flexibility?",
  discussionOptions: ["Review the buffer", "Map funding sources"],
  specialistSuggestion: "Consider a lending specialist.",
};

function readyState() {
  return workbenchReducer(createInitialState(), {
    type: "SOURCE_READY",
    artifactKind: "fixture",
    schemaVersion: "1.0.0",
  });
}

describe("workbench reducer invariants", () => {
  it("blocks case selection until a compatible source is ready", () => {
    const state = workbenchReducer(createInitialState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    expect(state.activeCaseId).toBeNull();
  });

  it("clears case-bound surface state when the active case changes", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, {
      type: "OPEN_SURFACE",
      caseId: "CASE-CL-0001",
      surface: "evidence",
      evidenceItemId: "E-H-LTV-AUG",
    });
    state = workbenchReducer(state, {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0003",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    expect(state.rightSurface).toBe("none");
    expect(state.activeEvidenceItemId).toBeNull();
  });

  it("rejects a surface request belonging to another case", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, {
      type: "OPEN_SURFACE",
      caseId: "CASE-CL-0003",
      surface: "evidence",
      evidenceItemId: "E-M-CONFLICT",
    });
    expect(state.rightSurface).toBe("none");
  });

  it("prepares revision 1 as a draft and requires explicit approval", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, { type: "PREPARE_BRIEF", caseId: "CASE-CL-0001", seed });
    expect(state.meetingBriefs["CASE-CL-0001"]).toMatchObject({
      revision: 1,
      status: "draft",
      approvedRevision: null,
    });
    state = workbenchReducer(state, { type: "APPROVE_BRIEF", caseId: "CASE-CL-0001" });
    expect(state.meetingBriefs["CASE-CL-0001"]).toMatchObject({ status: "approved", approvedRevision: 1 });
  });

  it("permits conversation-prepared only for the approved current revision", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, { type: "PREPARE_BRIEF", caseId: "CASE-CL-0001", seed });
    state = workbenchReducer(state, {
      type: "SET_CASE_RESOLUTION",
      caseId: "CASE-CL-0001",
      resolution: "conversation-prepared",
    });
    expect(state.caseResolutions["CASE-CL-0001"]).toBeUndefined();
    state = workbenchReducer(state, { type: "APPROVE_BRIEF", caseId: "CASE-CL-0001" });
    state = workbenchReducer(state, {
      type: "SET_CASE_RESOLUTION",
      caseId: "CASE-CL-0001",
      resolution: "conversation-prepared",
    });
    expect(state.caseResolutions["CASE-CL-0001"]).toEqual({
      state: "conversation-prepared",
      briefRevision: 1,
    });
  });

  it("editing an approved brief advances the revision and invalidates approval and resolution", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, { type: "PREPARE_BRIEF", caseId: "CASE-CL-0001", seed });
    state = workbenchReducer(state, { type: "APPROVE_BRIEF", caseId: "CASE-CL-0001" });
    state = workbenchReducer(state, {
      type: "SET_CASE_RESOLUTION",
      caseId: "CASE-CL-0001",
      resolution: "conversation-prepared",
    });
    state = workbenchReducer(state, {
      type: "EDIT_BRIEF_FIELD",
      caseId: "CASE-CL-0001",
      field: "openingQuestion",
      value: "What flexibility would feel right now?",
    });
    expect(state.meetingBriefs["CASE-CL-0001"]).toMatchObject({
      revision: 2,
      status: "draft",
      approvedRevision: null,
      edited: true,
    });
    expect(state.caseResolutions["CASE-CL-0001"]).toEqual({ state: "unresolved" });
  });

  it("resetting an approved brief creates a new unapproved revision and invalidates preparation", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, { type: "PREPARE_BRIEF", caseId: "CASE-CL-0001", seed });
    state = workbenchReducer(state, { type: "APPROVE_BRIEF", caseId: "CASE-CL-0001" });
    state = workbenchReducer(state, { type: "SET_CASE_RESOLUTION", caseId: "CASE-CL-0001", resolution: "conversation-prepared" });
    state = workbenchReducer(state, { type: "RESET_BRIEF", caseId: "CASE-CL-0001" });
    expect(state.meetingBriefs["CASE-CL-0001"]).toMatchObject({ revision: 2, status: "draft", approvedRevision: null, edited: false });
    expect(state.caseResolutions["CASE-CL-0001"]).toEqual({ state: "unresolved" });
  });

  it("requires a reason to dismiss a Client Case", () => {
    let state = workbenchReducer(readyState(), {
      type: "SELECT_CASE",
      caseId: "CASE-CL-0001",
      snapshots: ["2025-12-31", "2026-08-26"],
    });
    state = workbenchReducer(state, { type: "SET_CASE_RESOLUTION", caseId: "CASE-CL-0001", resolution: "dismissed" });
    expect(state.caseResolutions["CASE-CL-0001"]).toBeUndefined();
    state = workbenchReducer(state, { type: "SET_CASE_RESOLUTION", caseId: "CASE-CL-0001", resolution: "dismissed", reason: "Client confirmed no action is needed." });
    expect(state.caseResolutions["CASE-CL-0001"]).toEqual({ state: "dismissed", reason: "Client confirmed no action is needed." });
  });

  it("requires a reason to defer or dismiss an Open Loop", () => {
    const initial = readyState();
    const blocked = workbenchReducer(initial, {
      type: "SET_OPEN_LOOP_STATE",
      openLoopId: "OL-H-FAMILY",
      state: "deferred",
      note: " ",
    });
    expect(blocked.openLoopStates).toEqual({});
    const accepted = workbenchReducer(initial, {
      type: "SET_OPEN_LOOP_STATE",
      openLoopId: "OL-H-FAMILY",
      state: "dismissed",
      note: "Client confirmed this is no longer relevant.",
    });
    expect(accepted.openLoopStates["OL-H-FAMILY"]).toEqual({
      state: "dismissed",
      note: "Client confirmed this is no longer relevant.",
    });
  });

  it("keeps filter updates as presentation-only state", () => {
    const state = workbenchReducer(readyState(), {
      type: "SET_FILTERS",
      filters: { query: "Hartono", urgencyTiers: ["High"] },
    });
    expect(state.filters.query).toBe("Hartono");
    expect(state.filters.urgencyTiers).toEqual(["High"]);
  });
});
