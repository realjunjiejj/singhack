import type { ClientCase, EvidenceItem, EvidencePacket, WorkbenchModel } from "./types";

export function getCase(model: WorkbenchModel, caseId: string | null): ClientCase | null {
  return model.clientCases.find((item) => item.caseId === caseId) ?? null;
}

export function getCasePackets(model: WorkbenchModel, caseId: string): EvidencePacket[] {
  return model.evidencePackets.filter((packet) => packet.caseId === caseId);
}

export function getEvidenceItems(model: WorkbenchModel, caseId: string): EvidenceItem[] {
  return getCasePackets(model, caseId).flatMap((packet) => packet.items);
}

export function evidenceExists(model: WorkbenchModel, caseId: string, evidenceId: string) {
  return getCasePackets(model, caseId).some(
    (packet) => packet.items.some((item) => item.id === evidenceId) || packet.derivedMetrics.some((metric) => metric.id === evidenceId),
  );
}

export function quickFindCaseId(model: WorkbenchModel, clientId: string) {
  return model.book.priorityQueue.find((item) => item.clientId === clientId)?.caseId ?? null;
}
