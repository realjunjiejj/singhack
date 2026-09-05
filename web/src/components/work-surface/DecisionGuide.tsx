import type { ClientCase } from "@/lib/workbench/types";

export function DecisionGuide({ clientCase, onAction }: { clientCase: ClientCase; onAction: (action: string) => void }) {
  return (
    <div className="surface-content decision-guide">
      <div className="ai-status"><i aria-hidden="true" />AI-assisted insight ready</div>
      <p className="eyebrow">Next best conversation</p>
      <h2>Lead with the client’s priorities, not the alert.</h2>
      <blockquote>“{clientCase.meetingBrief.openingQuestion}”</blockquote>
      <div className="conversation-steps">
        <div><span>1</span><p><strong>Clarify</strong>{clientCase.meetingBrief.uncertainties[0] ?? "Confirm the client’s current objectives."}</p></div>
        <div><span>2</span><p><strong>Explore</strong>{clientCase.meetingBrief.discussionOptions[0] ?? "Review the supplied advisory options."}</p></div>
        <div><span>3</span><p><strong>Prepare</strong>Review evidence, then approve the Meeting Brief yourself.</p></div>
      </div>
      <div className="guide-actions">
        <button type="button" className="primary-button" onClick={() => onAction("prepare-conversation")}>Prepare Meeting Brief</button>
        <button type="button" onClick={() => onAction("show-evidence")}>Review evidence</button>
        {(clientCase.clientReadyDrafts?.length ?? 0) > 0 && <button type="button" onClick={() => onAction("client-ready")}>Open translation draft</button>}
      </div>
      <p className="boundary-note">Grounded in the current artifact. No action is sent or executed.</p>
    </div>
  );
}
