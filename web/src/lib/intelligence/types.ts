import type { Confidence, FactorContribution, Urgency, WorkbenchModel } from "@/lib/workbench/types";

export type NarrativeSource = "deterministic" | "model-validated";

export type IntelligenceFinding = {
  findingId: string;
  direction: string;
  clientId: string;
  caseId: string;
  title: string;
  summary: string;
  whyItMatters: string;
  limitations: string[];
  evidencePacketIds: string[];
  evidenceItemIds: string[];
  factorContributions: FactorContribution[];
  rank?: number;
  urgency?: Urgency;
  confidence?: Confidence;
  narrativeSource: NarrativeSource;
  narrativeEvidenceItemIds: string[];
};

export type AgentReport = {
  agentId: string;
  role: string;
  depth: "deep" | "supporting" | "control";
  status: "completed" | "partial" | "skipped" | "blocked";
  summary: string;
  findings: IntelligenceFinding[];
  diagnostics: Array<{ code: string; severity: string; message: string }>;
};

export type IntelligenceRun = {
  schemaVersion: string;
  runId: string;
  generatedAt: string;
  status: "completed" | "partial" | "needs-mapping" | "blocked";
  adapterId?: string;
  deepFocus: string[];
  diagnostics: Array<{ code: string; severity: string; message: string }>;
  agentReports: AgentReport[];
  workbench?: WorkbenchModel;
};

export function isIntelligenceRun(value: unknown): value is IntelligenceRun {
  if (!value || typeof value !== "object") return false;
  const run = value as Partial<IntelligenceRun>;
  return typeof run.runId === "string" && typeof run.status === "string" && Array.isArray(run.agentReports);
}
