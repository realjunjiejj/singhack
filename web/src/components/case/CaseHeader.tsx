import { ConfidenceBadge } from "@/components/common/ConfidenceBadge";
import { StatusBadge, UrgencyBadge } from "@/components/common/StatusBadge";
import type { ClientCase } from "@/lib/workbench/types";

import { CitationLink } from "@/components/common/CitationLink";

export function CaseHeader({
  clientCase,
  onEvidence,
  onPrepare,
}: {
  clientCase: ClientCase;
  onEvidence: (id: string) => void;
  onPrepare: () => void;
}) {
  const conclusionEvidence = Array.from(new Set(clientCase.facts.flatMap((claim) => claim.evidenceItemIds)));
  const whyNowEvidence = Array.from(new Set(clientCase.anticipatorySignals.flatMap((signal) => signal.evidenceItemIds)));
  return (
    <header className="case-header">
      <div className="case-identity">
        <div>
          <p className="eyebrow">Client Case · {clientCase.clientId}</p>
          <h1>{clientCase.clientName}</h1>
        </div>
        <div className="case-badges">
          <UrgencyBadge tier={clientCase.urgency.tier} score={clientCase.urgency.score} />
          <StatusBadge status={clientCase.status} />
        </div>
      </div>

      {/*
        BUILDER 2 NOTICE (UI ARCHITECTURE):
        Per product requirements, this block is designated "AI Advice".
        It MUST be placed at the very top part of each client profile (CaseHeader)
        so that Relationship Managers immediately see the contextual AI Advice
        (What needs attention, Why this matters now, and How to begin) before
        scrolling to client pulse, signals, open loops, or governance clocks.
      */}
      <details className="case-focus" aria-label="AI Advice">
        <summary>
          <span className="section-kicker">AI Advice · What needs attention</span>
          <span className="case-focus-summary">{clientCase.conclusion}</span>
          <span className="case-focus-toggle" aria-hidden="true"><span className="when-closed">Full context</span><span className="when-open">Less</span> <i>⌄</i></span>
        </summary>
        <div className="case-focus-detail">
          <span className="section-kicker">AI Advice · Why this matters now</span>
          <p>{clientCase.whyNow}</p>
          <CitationLink evidenceIds={whyNowEvidence} onOpen={onEvidence} />
        </div>
      </details>

      <div className="case-focus-meta">
        <CitationLink evidenceIds={conclusionEvidence} onOpen={onEvidence} />
        <ConfidenceBadge confidence={clientCase.confidence} />
      </div>
      {clientCase.urgency.safetyOverride && <p className="safety-override"><strong>Safety Override · {clientCase.urgency.safetyOverride.ruleId}</strong>{clientCase.urgency.safetyOverride.reason}</p>}

      <section className="conversation-start" aria-labelledby="conversation-start-title">
        <div>
          <span className="section-kicker">AI Advice · How to begin</span>
          <p id="conversation-start-title">“{clientCase.meetingBrief.openingQuestion}”</p>
        </div>
        <button className="primary-button" type="button" onClick={onPrepare}>Prepare conversation</button>
      </section>
    </header>
  );
}
