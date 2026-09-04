import type { ArtifactKind, MeetingBriefSeed, OpenLoopStateValue } from "@/lib/workbench/types";

export type RightSurface = "none" | "evidence" | "stress-test" | "meeting-brief" | "client-ready";
export type CaseResolutionState =
  | "unresolved"
  | "conversation-prepared"
  | "information-requested"
  | "specialist-involved"
  | "dismissed";

export type EditableBrief = Pick<
  MeetingBriefSeed,
  "whatChanged" | "whyItMatters" | "uncertainties" | "openingQuestion" | "discussionOptions" | "specialistSuggestion"
>;

export type MeetingBriefState = {
  revision: number;
  status: "draft" | "approved";
  approvedRevision: number | null;
  fields: EditableBrief;
  sourceFields: EditableBrief;
  edited: boolean;
};

export type WorkbenchState = {
  source: {
    status: "loading" | "ready" | "error";
    artifactKind?: ArtifactKind;
    schemaVersion?: string;
    error?: string;
  };
  activeCaseId: string | null;
  filters: {
    query: string;
    signalTypes: string[];
    bookingCentres: string[];
    urgencyTiers: string[];
    confidenceLevels: string[];
  };
  rightSurface: RightSurface;
  activeEvidenceItemId: string | null;
  selectedSnapshots: [string, string];
  selectedStressScenarioId: string | null;
  openLoopStates: Record<string, { state: OpenLoopStateValue; note?: string }>;
  meetingBriefs: Record<string, MeetingBriefState>;
  caseResolutions: Record<
    string,
    { state: CaseResolutionState; reason?: string; briefRevision?: number }
  >;
};

export function createInitialState(): WorkbenchState {
  return {
    source: { status: "loading" },
    activeCaseId: null,
    filters: {
      query: "",
      signalTypes: [],
      bookingCentres: [],
      urgencyTiers: [],
      confidenceLevels: [],
    },
    rightSurface: "none",
    activeEvidenceItemId: null,
    selectedSnapshots: ["", ""],
    selectedStressScenarioId: null,
    openLoopStates: {},
    meetingBriefs: {},
    caseResolutions: {},
  };
}
