import { EmptyState } from "@/components/common/EmptyState";
import type { CaseResolutionState, EditableBrief, WorkbenchState } from "@/lib/state/model";
import { getCasePackets } from "@/lib/workbench/selectors";
import type { ClientCase, WorkbenchModel } from "@/lib/workbench/types";
import { ClientReadyView } from "./ClientReadyView";
import { EvidenceChain } from "./EvidenceChain";
import { MeetingBrief } from "./MeetingBrief";
import { StressTest } from "./StressTest";
import { DecisionGuide } from "./DecisionGuide";

const titles = {
  none: "Advisory path",
  evidence: "Evidence Chain",
  "stress-test": "Collateral Stress Test",
  "meeting-brief": "Meeting Brief",
  "client-ready": "Client-Ready View",
};

export function WorkSurface({
  model,
  clientCase,
  state,
  onClose,
  onEvidence,
  onBack,
  onScenario,
  onEditBrief,
  onResetBrief,
  onApproveBrief,
  onResolve,
  onGuidedAction,
}: {
  model: WorkbenchModel;
  clientCase: ClientCase | null;
  state: WorkbenchState;
  onClose: () => void;
  onEvidence: (id: string) => void;
  onBack: () => void;
  onScenario: (id: string) => void;
  onEditBrief: (field: keyof EditableBrief, value: EditableBrief[keyof EditableBrief]) => void;
  onResetBrief: () => void;
  onApproveBrief: () => void;
  onResolve: (state: CaseResolutionState, reason?: string) => void;
  onGuidedAction: (action: string) => void;
}) {
  return (
    <aside className={`work-surface surface-${state.rightSurface} ${state.rightSurface !== "none" ? "is-open" : ""}`} aria-labelledby="surface-title">
      <div className="column-header surface-header">
        <div><p className="eyebrow">{state.rightSurface === "none" ? "Understand → Prepare" : "Prepare"}</p><h2 id="surface-title">{titles[state.rightSurface]}</h2></div>
        {state.rightSurface !== "none" && <button type="button" className="icon-button" onClick={onClose} aria-label="Close work surface">×</button>}
      </div>
      {!clientCase ? (
        <EmptyState title="No preparation open" body="Select a Client Case first." />
      ) : state.rightSurface === "none" ? (
        <DecisionGuide clientCase={clientCase} onAction={onGuidedAction} />
      ) : state.rightSurface === "evidence" ? (
        <EvidenceChain packets={getCasePackets(model, clientCase.caseId)} activeEvidenceItemId={state.activeEvidenceItemId} onEvidence={onEvidence} onBack={onBack} />
      ) : state.rightSurface === "stress-test" ? (
        <StressTest stressTest={clientCase.collateralStressTest} selectedScenarioId={state.selectedStressScenarioId} onSelect={onScenario} />
      ) : state.rightSurface === "meeting-brief" ? (
        <MeetingBrief clientCase={clientCase} brief={state.meetingBriefs[clientCase.caseId]} resolution={state.caseResolutions[clientCase.caseId]} onEdit={onEditBrief} onReset={onResetBrief} onApprove={onApproveBrief} onResolve={onResolve} onEvidence={onEvidence} />
      ) : (
        <ClientReadyView clientCase={clientCase} brief={state.meetingBriefs[clientCase.caseId]} onEvidence={onEvidence} />
      )}
    </aside>
  );
}
