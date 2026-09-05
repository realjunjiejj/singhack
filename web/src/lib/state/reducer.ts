import type { EditableBrief, WorkbenchState } from "./model";
import { createInitialState } from "./model";
import type { ArtifactKind, OpenLoopStateValue } from "@/lib/workbench/types";
import type { CaseResolutionState, RightSurface } from "./model";

type Action =
  | { type: "SOURCE_READY"; artifactKind: ArtifactKind; schemaVersion: string }
  | { type: "SOURCE_ERROR"; error: string; schemaVersion?: string }
  | { type: "SELECT_CASE"; caseId: string; snapshots: [string, string]; stressScenarioId?: string | null }
  | { type: "SET_FILTERS"; filters: Partial<WorkbenchState["filters"]> }
  | {
      type: "OPEN_SURFACE";
      caseId: string;
      surface: RightSurface;
      evidenceItemId?: string | null;
    }
  | { type: "CLOSE_SURFACE" }
  | { type: "SELECT_EVIDENCE"; caseId: string; evidenceItemId: string }
  | { type: "SELECT_SNAPSHOTS"; snapshots: [string, string] }
  | { type: "SELECT_STRESS_SCENARIO"; scenarioId: string }
  | { type: "SET_OPEN_LOOP_STATE"; openLoopId: string; state: OpenLoopStateValue; note?: string }
  | { type: "PREPARE_BRIEF"; caseId: string; seed: EditableBrief }
  | {
      type: "EDIT_BRIEF_FIELD";
      caseId: string;
      field: keyof EditableBrief;
      value: EditableBrief[keyof EditableBrief];
    }
  | { type: "RESET_BRIEF"; caseId: string }
  | { type: "APPROVE_BRIEF"; caseId: string }
  | { type: "SET_CASE_RESOLUTION"; caseId: string; resolution: CaseResolutionState; reason?: string };

function isActiveReadyCase(state: WorkbenchState, caseId: string) {
  return state.source.status === "ready" && state.activeCaseId === caseId;
}

function invalidatePreparedResolution(state: WorkbenchState, caseId: string) {
  if (state.caseResolutions[caseId]?.state !== "conversation-prepared") return state.caseResolutions;
  return { ...state.caseResolutions, [caseId]: { state: "unresolved" as const } };
}

export function workbenchReducer(state: WorkbenchState, action: Action): WorkbenchState {
  switch (action.type) {
    case "SOURCE_READY":
      return {
        // Approvals and decisions belong to the adopted dataset, not IDs alone.
        ...createInitialState(),
        source: {
          status: "ready",
          artifactKind: action.artifactKind,
          schemaVersion: action.schemaVersion,
        },
      };
    case "SOURCE_ERROR":
      return {
        ...state,
        source: { status: "error", error: action.error, schemaVersion: action.schemaVersion },
        activeCaseId: null,
        rightSurface: "none",
        activeEvidenceItemId: null,
      };
    case "SELECT_CASE":
      if (state.source.status !== "ready") return state;
      return {
        ...state,
        activeCaseId: action.caseId,
        rightSurface: "none",
        activeEvidenceItemId: null,
        selectedSnapshots: action.snapshots,
        selectedStressScenarioId: action.stressScenarioId ?? null,
      };
    case "SET_FILTERS":
      return { ...state, filters: { ...state.filters, ...action.filters } };
    case "OPEN_SURFACE":
      if (!isActiveReadyCase(state, action.caseId)) return state;
      return {
        ...state,
        rightSurface: action.surface,
        activeEvidenceItemId: action.surface === "evidence" ? action.evidenceItemId ?? null : null,
      };
    case "CLOSE_SURFACE":
      return { ...state, rightSurface: "none", activeEvidenceItemId: null };
    case "SELECT_EVIDENCE":
      if (!isActiveReadyCase(state, action.caseId)) return state;
      return { ...state, rightSurface: "evidence", activeEvidenceItemId: action.evidenceItemId };
    case "SELECT_SNAPSHOTS":
      return { ...state, selectedSnapshots: action.snapshots };
    case "SELECT_STRESS_SCENARIO":
      return { ...state, selectedStressScenarioId: action.scenarioId };
    case "SET_OPEN_LOOP_STATE": {
      const note = action.note?.trim();
      if (["deferred", "dismissed"].includes(action.state) && !note) return state;
      return {
        ...state,
        openLoopStates: {
          ...state.openLoopStates,
          [action.openLoopId]: { state: action.state, ...(note ? { note } : {}) },
        },
      };
    }
    case "PREPARE_BRIEF":
      if (!isActiveReadyCase(state, action.caseId)) return state;
      return {
        ...state,
        rightSurface: "meeting-brief",
        activeEvidenceItemId: null,
        meetingBriefs: {
          ...state.meetingBriefs,
          [action.caseId]:
            state.meetingBriefs[action.caseId] ?? {
              revision: 1,
              status: "draft",
              approvedRevision: null,
              fields: structuredClone(action.seed),
              sourceFields: structuredClone(action.seed),
              edited: false,
            },
        },
      };
    case "EDIT_BRIEF_FIELD": {
      if (!isActiveReadyCase(state, action.caseId)) return state;
      const brief = state.meetingBriefs[action.caseId];
      if (!brief) return state;
      const wasApproved = brief.status === "approved";
      return {
        ...state,
        meetingBriefs: {
          ...state.meetingBriefs,
          [action.caseId]: {
            ...brief,
            revision: wasApproved ? brief.revision + 1 : brief.revision,
            status: "draft",
            approvedRevision: null,
            edited: true,
            fields: { ...brief.fields, [action.field]: action.value },
          },
        },
        caseResolutions: invalidatePreparedResolution(state, action.caseId),
      };
    }
    case "RESET_BRIEF": {
      if (!isActiveReadyCase(state, action.caseId)) return state;
      const brief = state.meetingBriefs[action.caseId];
      if (!brief) return state;
      const wasApproved = brief.status === "approved";
      return {
        ...state,
        meetingBriefs: {
          ...state.meetingBriefs,
          [action.caseId]: {
            ...brief,
            revision: wasApproved ? brief.revision + 1 : brief.revision,
            status: "draft",
            approvedRevision: null,
            fields: structuredClone(brief.sourceFields),
            edited: false,
          },
        },
        caseResolutions: invalidatePreparedResolution(state, action.caseId),
      };
    }
    case "APPROVE_BRIEF": {
      if (!isActiveReadyCase(state, action.caseId)) return state;
      const brief = state.meetingBriefs[action.caseId];
      if (!brief || brief.status !== "draft") return state;
      return {
        ...state,
        meetingBriefs: {
          ...state.meetingBriefs,
          [action.caseId]: { ...brief, status: "approved", approvedRevision: brief.revision },
        },
      };
    }
    case "SET_CASE_RESOLUTION": {
      if (!isActiveReadyCase(state, action.caseId)) return state;
      const reason = action.reason?.trim();
      if (action.resolution === "dismissed" && !reason) return state;
      if (action.resolution === "conversation-prepared") {
        const brief = state.meetingBriefs[action.caseId];
        if (!brief || brief.status !== "approved" || brief.approvedRevision !== brief.revision) return state;
        return {
          ...state,
          caseResolutions: {
            ...state.caseResolutions,
            [action.caseId]: { state: action.resolution, briefRevision: brief.revision },
          },
        };
      }
      return {
        ...state,
        caseResolutions: {
          ...state.caseResolutions,
          [action.caseId]: { state: action.resolution, ...(reason ? { reason } : {}) },
        },
      };
    }
    default:
      return state;
  }
}

export type WorkbenchAction = Action;
