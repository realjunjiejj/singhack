import { CitationLink } from "@/components/common/CitationLink";
import { EmptyState } from "@/components/common/EmptyState";
import { FactorBreakdown } from "@/components/queue/FactorBreakdown";
import type { WorkbenchState } from "@/lib/state/model";
import type { ClientCase } from "@/lib/workbench/types";
import { CaseHeader } from "./CaseHeader";
import { GovernanceClocks } from "./GovernanceClocks";
import { OpenLoops } from "./OpenLoops";
import { SignalList } from "./SignalList";
import { SnapshotComparison } from "./SnapshotComparison";

export function ClientCasePanel({
  clientCase,
  state,
  onEvidence,
  onOpenLoop,
  onSnapshots,
  onGuidedAction,
}: {
  clientCase: ClientCase | null;
  state: WorkbenchState;
  onEvidence: (id: string) => void;
  onOpenLoop: (id: string, value: Parameters<typeof OpenLoops>[0]["loops"][number]["state"], note?: string) => void;
  onSnapshots: (value: [string, string]) => void;
  onGuidedAction: (action: string) => void;
}) {
  if (!clientCase) return <section className="case-column"><EmptyState title="No Client Case selected" body="Choose a case from the Priority Queue to understand why it matters now." /></section>;
  const claimGroups = [
    { title: "Facts", className: "fact", claims: clientCase.facts },
    { title: "Interpretations", className: "interpretation", claims: clientCase.interpretations },
    { title: "Uncertainties", className: "uncertainty", claims: clientCase.uncertainties },
  ];
  return (
    <main className="case-column" id="active-client-case" tabIndex={-1}>
      <CaseHeader clientCase={clientCase} onEvidence={onEvidence} />
      <section className="case-section thread-section" aria-labelledby="case-thread-title">
        <div className="section-heading"><div><p className="eyebrow">Signal → Evidence → Conversation</p><h2 id="case-thread-title">Case thread</h2></div></div>
        <div className="claim-grid">
          {claimGroups.map((group) => (
            <div className={`claim-group ${group.className}`} key={group.title}>
              <h3>{group.title}</h3>
              {group.claims.length === 0 ? <p className="muted">None supplied.</p> : group.claims.map((claim) => (
                <p key={claim.id}>{claim.statement} <CitationLink evidenceIds={claim.evidenceItemIds} onOpen={onEvidence} /></p>
              ))}
            </div>
          ))}
        </div>
      </section>
      <section className="case-section"><h2>Visible Priority Rationale</h2><FactorBreakdown factors={clientCase.factorContributions} onEvidence={onEvidence} /></section>
      <SignalList signals={clientCase.anticipatorySignals} onEvidence={onEvidence} />
      <OpenLoops loops={clientCase.openLoops} states={state.openLoopStates} onEvidence={onEvidence} onDecision={onOpenLoop} />
      <GovernanceClocks clocks={clientCase.governanceClocks} onEvidence={onEvidence} />
      <SnapshotComparison timeline={clientCase.timeline} selected={state.selectedSnapshots} onSelect={onSnapshots} onEvidence={onEvidence} />
      {(clientCase.collateralStressTest || (clientCase.clientReadyDrafts?.length ?? 0) > 0) && (
        <section className="case-section prepared-views" aria-labelledby="prepared-views-title">
          <h2 id="prepared-views-title">Prepared views</h2>
          <div className="action-row">
            {clientCase.collateralStressTest && <button type="button" onClick={() => onGuidedAction("stress-test")}>Explore supplied collateral what-if</button>}
            {(clientCase.clientReadyDrafts?.length ?? 0) > 0 && <button type="button" onClick={() => onGuidedAction("client-ready")}>Review Client-Ready View</button>}
          </div>
        </section>
      )}
      <section className="case-section guided-actions" aria-labelledby="guided-actions-title">
        <p className="eyebrow">Bounded requests</p><h2 id="guided-actions-title">Guided Actions</h2>
        <div className="action-row">
          {clientCase.allowedGuidedActions.map((action) => (
            <button type="button" key={action} onClick={() => onGuidedAction(action)}>{action.replace(/-/g, " ")}</button>
          ))}
        </div>
        <p className="boundary-note">These actions prepare RM review only. Nothing is sent, traded, scheduled, or persisted.</p>
      </section>
    </main>
  );
}
