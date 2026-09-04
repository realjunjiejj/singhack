import type { WorkbenchState } from "./model";
import type { ClientCase, PriorityQueueItem, WorkbenchModel } from "@/lib/workbench/types";

export function filterPriorityQueue(
  rows: PriorityQueueItem[],
  filters: WorkbenchState["filters"],
  clientCases: ClientCase[] = [],
): PriorityQueueItem[] {
  const query = filters.query.trim().toLocaleLowerCase();
  return rows.filter((row) => {
    const matchesQuery =
      !query ||
      [row.clientName, row.clientId, row.priorityRationale, ...row.signalSummaries]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query);
    const caseSignalTypes = clientCases
      .find((clientCase) => clientCase.caseId === row.caseId)
      ?.anticipatorySignals.map((signal) => signal.type.toLocaleLowerCase()) ?? [];
    const matchesSignals =
      filters.signalTypes.length === 0 ||
      filters.signalTypes.some((signal) => {
        const normalized = signal.toLocaleLowerCase();
        return caseSignalTypes.includes(normalized) || row.signalSummaries.some((summary) => summary.toLocaleLowerCase().includes(normalized));
      });
    return (
      matchesQuery &&
      matchesSignals &&
      (filters.bookingCentres.length === 0 || filters.bookingCentres.includes(row.bookingCentre)) &&
      (filters.urgencyTiers.length === 0 || filters.urgencyTiers.includes(row.urgency.tier)) &&
      (filters.confidenceLevels.length === 0 || filters.confidenceLevels.includes(row.confidence.level))
    );
  });
}

export function activeCase(model: WorkbenchModel, state: WorkbenchState) {
  return model.clientCases.find((item) => item.caseId === state.activeCaseId) ?? null;
}
