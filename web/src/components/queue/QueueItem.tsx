import { useState } from "react";
import { ConfidenceBadge } from "@/components/common/ConfidenceBadge";
import { StatusBadge, UrgencyBadge } from "@/components/common/StatusBadge";
import type { PriorityQueueItem } from "@/lib/workbench/types";
import { FactorBreakdown } from "./FactorBreakdown";

export function QueueItem({ item, active, onSelect, onEvidence }: { item: PriorityQueueItem; active: boolean; onSelect: () => void; onEvidence?: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <article className={`queue-item ${active ? "is-active" : ""}`} aria-current={active ? "true" : undefined}>
      <button type="button" className="queue-select" onClick={onSelect}>
        <span className="rank">{String(item.rank).padStart(2, "0")}</span>
        <span className="queue-main">
          <strong className="client-name">{item.clientName}</strong>
          <span className="client-meta">{item.clientId} · {item.bookingCentre}</span>
          <span className="queue-badges"><UrgencyBadge tier={item.urgency.tier} score={item.urgency.score} /></span>
          <span className="rationale">{item.priorityRationale}</span>
          <StatusBadge status={item.status} />
          <span className="queue-summary">{item.signalSummaries.length} signals · {item.openLoopCount} Open Loops · {item.governanceClockCount} Governance</span>
          <ConfidenceBadge confidence={item.confidence} />
        </span>
      </button>
      <button className="factor-toggle" type="button" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
        {expanded ? "Hide" : "Show"} Priority Rationale factors <span aria-hidden="true">{expanded ? "−" : "+"}</span>
      </button>
      {expanded && <FactorBreakdown factors={item.factorContributions} onEvidence={onEvidence} />}
    </article>
  );
}
