export const SUPPORTED_SCHEMA_VERSION = "1.0.0";

export type ArtifactKind = "fixture" | "generated";
export type UrgencyTier = "Critical" | "High" | "Watch";
export type ConfidenceLevel = "High" | "Medium" | "Low";
export type CaseStatus = "active" | "near" | "historical-resolved" | "normal";
export type GuidedAction =
  | "explain"
  | "show-evidence"
  | "prepare-conversation"
  | "request-information"
  | "involve-specialist"
  | "confirm-open-loop"
  | "defer-open-loop"
  | "assign-open-loop"
  | "dismiss-open-loop"
  | "dismiss-case";

export type SourceReference = { file: string; recordKey: string; field?: string };
export type Claim = { id: string; statement: string; evidenceItemIds: string[] };
export type Money = { amount: number; currency: string };
export type Measure = { value: number; unit: string; currency?: string };
export type Urgency = {
  tier: UrgencyTier;
  score: number;
  safetyOverride: null | { ruleId: string; reason: string };
};
export type Confidence = { level: ConfidenceLevel; score: number; reasons: string[] };
export type FactorContribution = {
  factor: string;
  points: number;
  reason: string;
  evidenceItemIds: string[];
};
export type PriorityQueueItem = {
  rank: number;
  caseId: string;
  clientId: string;
  clientName: string;
  bookingCentre: string;
  reportingLanguage: string;
  urgency: Urgency;
  confidence: Confidence;
  priorityRationale: string;
  factorContributions: FactorContribution[];
  status: CaseStatus;
  signalSummaries: string[];
  openLoopCount: number;
  governanceClockCount: number;
};
export type AnticipatorySignal = {
  id: string;
  type: string;
  status: CaseStatus;
  summary: string;
  timeHorizon: string;
  evidenceItemIds: string[];
};
export type OpenLoop = {
  id: string;
  summary: string;
  noteDate: string;
  sourceExcerpt: string;
  whyOpen: string;
  confidence: Confidence;
  confirmationRequired: true;
  state: OpenLoopStateValue;
  evidenceItemIds: string[];
};
export type GovernanceClock = {
  id: string;
  type: string;
  dueDate: string;
  daysRemaining: number;
  status: "due-soon" | "due-today" | "overdue" | "future";
  summary: string;
  evidenceItemIds: string[];
};
export type TimelinePoint = {
  date: string;
  label: string;
  metrics: Record<string, Measure>;
  evidenceItemIds: string[];
};
export type MeetingBriefSeed = {
  whatChanged: string;
  whyItMatters: string;
  uncertainties: string[];
  openingQuestion: string;
  discussionOptions: string[];
  specialistSuggestion: string | null;
  openLoopIds: string[];
  governanceClockIds: string[];
  evidenceItemIds: string[];
};
export type ClientReadyDraft = {
  language: string;
  canonicalLanguage: string;
  status: "draft";
  content: string;
  evidenceItemIds: string[];
};
export type StressScenario = {
  id: string;
  collateralChangePct: number;
  collateralValue: Money;
  lendingValue: Money;
  drawnAmount: Money;
  ltvPct: number;
  triggerPct: number;
  distanceToTriggerPctPoints: number;
  status: CaseStatus;
};
export type ClientCase = {
  caseId: string;
  clientId: string;
  clientName: string;
  reportingLanguage: string;
  conclusion: string;
  whyNow: string;
  status: CaseStatus;
  urgency: Urgency;
  confidence: Confidence;
  facts: Claim[];
  interpretations: Claim[];
  uncertainties: Claim[];
  factorContributions: FactorContribution[];
  anticipatorySignals: AnticipatorySignal[];
  openLoops: OpenLoop[];
  governanceClocks: GovernanceClock[];
  timeline: TimelinePoint[];
  evidencePacketIds: string[];
  allowedGuidedActions: GuidedAction[];
  meetingBrief: MeetingBriefSeed;
  clientReadyDrafts?: ClientReadyDraft[];
  collateralStressTest?: { label: string; forecast: false; scenarios: StressScenario[] };
};
export type EvidenceItem = {
  id: string;
  label: string;
  value: unknown;
  sourceReference: SourceReference;
};
export type DerivedMetric = {
  id: string;
  name: string;
  formula: string;
  inputs: Record<string, unknown>;
  result: Measure;
  snapshotDate: string;
};
export type EvidencePacket = {
  packetId: string;
  caseId: string;
  clientId: string;
  asOfDate: string;
  signalType: string;
  status: CaseStatus;
  facts: Claim[];
  interpretations: Claim[];
  uncertainties: Claim[];
  conflicts: Claim[];
  assumptions: Claim[];
  urgencyInputs: FactorContribution[];
  confidenceInputs: string[];
  derivedMetrics: DerivedMetric[];
  items: EvidenceItem[];
  allowedGuidedActions: GuidedAction[];
};
export type WorkbenchModel = {
  meta: {
    schemaVersion: string;
    artifactKind: ArtifactKind;
    asOfDate: string;
    generatedAt: string;
    sourceSnapshotDates: string[];
    dataQuality: {
      status: "clear" | "attention" | "blocked";
      issues: Array<{
        id: string;
        severity: "info" | "warning" | "material";
        summary: string;
        sourceReferences: SourceReference[];
      }>;
    };
  };
  book: {
    rm: { id: string; name: string };
    clientCount: number;
    portfolioCount: number;
    summary: { critical: number; high: number; watch: number };
    filters: {
      signalTypes: string[];
      bookingCentres: string[];
      urgencyTiers: UrgencyTier[];
      confidenceLevels: ConfidenceLevel[];
    };
    priorityQueue: PriorityQueueItem[];
  };
  clientCases: ClientCase[];
  evidencePackets: EvidencePacket[];
};

export type OpenLoopStateValue = "candidate" | "confirmed" | "deferred" | "assigned" | "dismissed";
