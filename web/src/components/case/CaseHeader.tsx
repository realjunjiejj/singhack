import { ConfidenceBadge } from "@/components/common/ConfidenceBadge";
import { StatusBadge, UrgencyBadge } from "@/components/common/StatusBadge";
import type { ClientCase } from "@/lib/workbench/types";

import { CitationLink } from "@/components/common/CitationLink";

export function CaseHeader({ clientCase, onEvidence }: { clientCase: ClientCase; onEvidence: (id: string) => void }) {
  const conclusionEvidence = Array.from(new Set(clientCase.facts.flatMap((claim) => claim.evidenceItemIds)));
  const whyNowEvidence = Array.from(new Set(clientCase.anticipatorySignals.flatMap((signal) => signal.evidenceItemIds)));
  return (
    <header className="case-header">
      <p className="eyebrow">Client Case · {clientCase.clientId}</p>
      <h1>{clientCase.clientName}</h1>
      <div className="case-badges">
        <UrgencyBadge tier={clientCase.urgency.tier} score={clientCase.urgency.score} />
        <StatusBadge status={clientCase.status} />
      </div>
      <div className="conclusion-block">
        <span className="section-kicker">Conclusion</span>
        <p>{clientCase.conclusion}</p>
        <CitationLink evidenceIds={conclusionEvidence} onOpen={onEvidence} />
      </div>
      <div className="why-now">
        <span className="thread-node" aria-hidden="true">1</span>
        <div><span className="section-kicker">Why now</span><p>{clientCase.whyNow}</p><CitationLink evidenceIds={whyNowEvidence} onOpen={onEvidence} /></div>
      </div>
      {clientCase.urgency.safetyOverride && <p className="safety-override"><strong>Safety Override · {clientCase.urgency.safetyOverride.ruleId}</strong>{clientCase.urgency.safetyOverride.reason}</p>}
      <ConfidenceBadge confidence={clientCase.confidence} showReasons />
    </header>
  );
}
