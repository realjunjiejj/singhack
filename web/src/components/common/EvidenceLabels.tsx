"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";
import type { WorkbenchModel } from "@/lib/workbench/types";

const EvidenceLabelsContext = createContext<Record<string, string>>({});

export function EvidenceLabelsProvider({ model, children }: { model: WorkbenchModel; children: ReactNode }) {
  const labels = useMemo(() => {
    const next: Record<string, string> = {};
    for (const packet of model.evidencePackets) {
      for (const item of packet.items) next[item.id] = item.label;
      for (const metric of packet.derivedMetrics) next[metric.id] = metric.name;
    }
    return next;
  }, [model]);

  return <EvidenceLabelsContext.Provider value={labels}>{children}</EvidenceLabelsContext.Provider>;
}

export function useEvidenceLabels() {
  return useContext(EvidenceLabelsContext);
}
