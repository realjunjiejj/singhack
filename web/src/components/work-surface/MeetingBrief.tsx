import { useState } from "react";
import { CitationLink } from "@/components/common/CitationLink";
import type { CaseResolutionState, EditableBrief, MeetingBriefState } from "@/lib/state/model";
import type { ClientCase } from "@/lib/workbench/types";

export function MeetingBrief({
  clientCase,
  brief,
  resolution,
  onEdit,
  onReset,
  onApprove,
  onResolve,
  onEvidence,
}: {
  clientCase: ClientCase;
  brief: MeetingBriefState | undefined;
  resolution: { state: CaseResolutionState; reason?: string; briefRevision?: number } | undefined;
  onEdit: (field: keyof EditableBrief, value: EditableBrief[keyof EditableBrief]) => void;
  onReset: () => void;
  onApprove: () => void;
  onResolve: (state: CaseResolutionState, reason?: string) => void;
  onEvidence: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [dismissReason, setDismissReason] = useState("");
  const [dismissError, setDismissError] = useState(false);
  if (!brief) return <div className="surface-content"><p className="muted">Prepare a conversation to create the source-backed Meeting Brief.</p></div>;
  const statusLabel = brief.status === "approved" ? `Approved revision ${brief.approvedRevision}` : brief.edited ? `Edited draft · revision ${brief.revision}` : `Draft · revision ${brief.revision}`;
  const setString = (field: keyof EditableBrief) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onEdit(field, event.target.value);
  return (
    <div className="surface-content meeting-brief">
      <div className={`brief-status ${brief.status}`}><span>{statusLabel}</span><strong>RM review required</strong></div>
      <div className="guardrail-banner">Internal preparation only · No client-facing send · Facts remain tied to the Evidence Packet</div>
      <div className="brief-actions">
        <button type="button" onClick={() => setEditing((value) => !value)}>{editing ? "Finish editing" : "Edit"}</button>
        <button type="button" onClick={onReset}>Reset to source seed</button>
        <button type="button" className="primary-button" onClick={onApprove} disabled={brief.status === "approved"}>Approve</button>
      </div>
      <BriefField label="What changed" value={brief.fields.whatChanged} editing={editing} onChange={setString("whatChanged")} />
      <BriefField label="Why it matters now" value={brief.fields.whyItMatters} editing={editing} onChange={setString("whyItMatters")} />
      <BriefField label="Respectful opening question" value={brief.fields.openingQuestion} editing={editing} onChange={setString("openingQuestion")} />
      <section className="brief-section"><h3>Uncertainties and conflicts</h3>
        {editing ? <textarea aria-label="Uncertainties and conflicts" value={brief.fields.uncertainties.join("\n")} onChange={(event) => onEdit("uncertainties", event.target.value.split("\n").filter(Boolean))} /> : <ul>{brief.fields.uncertainties.map((item) => <li key={item}>{item}</li>)}</ul>}
      </section>
      <section className="brief-section"><h3>Discussion options</h3>
        {editing ? <textarea aria-label="Discussion options" value={brief.fields.discussionOptions.join("\n")} onChange={(event) => onEdit("discussionOptions", event.target.value.split("\n").filter(Boolean))} /> : <ol>{brief.fields.discussionOptions.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ol>}
      </section>
      <BriefField label="Specialist suggestion" value={brief.fields.specialistSuggestion ?? "None supplied"} editing={editing} onChange={setString("specialistSuggestion")} />
      <section className="brief-section"><h3>Factual evidence citations</h3><CitationLink evidenceIds={clientCase.meetingBrief.evidenceItemIds} onOpen={onEvidence} /></section>
      <section className="brief-section"><h3>Relationship and governance</h3>
        <p>{clientCase.meetingBrief.openLoopIds.length} Open Loops · {clientCase.meetingBrief.governanceClockIds.length} Governance Clocks</p>
      </section>
      <section className="brief-section"><h3>Approved Guided Actions</h3><p>{clientCase.allowedGuidedActions.map((action) => action.replace(/-/g, " ")).join(" · ")}</p></section>
      <section className="resolution-panel" aria-labelledby="resolution-title">
        <p className="eyebrow">Human-controlled outcome</p><h3 id="resolution-title">Case Resolution</h3>
        <p>Current · <strong>{resolution?.state.replace(/-/g, " ") ?? "unresolved"}</strong>{resolution?.briefRevision ? ` · brief revision ${resolution.briefRevision}` : ""}</p>
        <button type="button" className="primary-button" disabled={brief.status !== "approved"} onClick={() => onResolve("conversation-prepared")}>Mark conversation prepared</button>
        <div className="action-row compact-actions">
          <button type="button" onClick={() => onResolve("information-requested")}>Request information</button>
          <button type="button" onClick={() => onResolve("specialist-involved")}>Involve specialist</button>
        </div>
        <label className="note-field">Dismissal reason
          <input value={dismissReason} onChange={(event) => { setDismissReason(event.target.value); setDismissError(false); }} placeholder="Required to dismiss case" aria-invalid={dismissError || undefined} aria-describedby={dismissError ? "dismiss-case-error" : undefined} />
        </label>
        {dismissError && <p className="field-error" id="dismiss-case-error">Add a reason before dismissing this Client Case.</p>}
        <button type="button" className="danger-button" onClick={() => { if (!dismissReason.trim()) { setDismissError(true); return; } onResolve("dismissed", dismissReason); }}>Dismiss case</button>
      </section>
    </div>
  );
}

function BriefField({ label, value, editing, onChange }: { label: string; value: string; editing: boolean; onChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void }) {
  return <section className="brief-section"><h3>{label}</h3>{editing ? <textarea aria-label={label} value={value} onChange={onChange} /> : <p>{value}</p>}</section>;
}
