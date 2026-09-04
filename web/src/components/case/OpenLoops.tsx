import { useState } from "react";
import { CitationLink } from "@/components/common/CitationLink";
import { ConfidenceBadge } from "@/components/common/ConfidenceBadge";
import { StateBadge } from "@/components/common/StatusBadge";
import type { WorkbenchState } from "@/lib/state/model";
import { formatDate } from "@/lib/workbench/format";
import type { OpenLoop, OpenLoopStateValue } from "@/lib/workbench/types";

export function OpenLoops({
  loops,
  states,
  onEvidence,
  onDecision,
}: {
  loops: OpenLoop[];
  states: WorkbenchState["openLoopStates"];
  onEvidence: (id: string) => void;
  onDecision: (id: string, state: OpenLoopStateValue, note?: string) => void;
}) {
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, boolean>>({});
  const decide = (id: string, state: OpenLoopStateValue) => {
    const note = notes[id]?.trim();
    if (["deferred", "dismissed"].includes(state) && !note) {
      setErrors({ ...errors, [id]: true });
      return;
    }
    setErrors({ ...errors, [id]: false });
    onDecision(id, state, note);
  };
  return (
    <section className="case-section" aria-labelledby="loops-title">
      <p className="relationship-frame">The threads at risk of being dropped</p>
      <h2 id="loops-title">Open Loops</h2>
      {loops.length === 0 ? <p className="muted">No Open Loop candidates supplied.</p> : loops.map((loop) => {
        const current = states[loop.id] ?? { state: loop.state };
        return (
          <article className="open-loop" key={loop.id}>
            <div className="card-topline"><StateBadge value={current.state} /><time dateTime={loop.noteDate}>{formatDate(loop.noteDate)}</time></div>
            <h3>{loop.summary}</h3>
            <blockquote>“{loop.sourceExcerpt}”</blockquote>
            <p>{loop.whyOpen}</p>
            <ConfidenceBadge confidence={loop.confidence} />
            <CitationLink evidenceIds={loop.evidenceItemIds} onOpen={onEvidence} />
            <label className="note-field">
              <span>Reason/note <small>(required for defer or dismiss)</small></span>
              <input value={notes[loop.id] ?? ""} onChange={(event) => { setNotes({ ...notes, [loop.id]: event.target.value }); setErrors({ ...errors, [loop.id]: false }); }} placeholder="Add RM context" aria-invalid={errors[loop.id] || undefined} aria-describedby={errors[loop.id] ? `loop-error-${loop.id}` : undefined} />
            </label>
            {errors[loop.id] && <p className="field-error" id={`loop-error-${loop.id}`}>Add a brief reason before deferring or dismissing this Open Loop.</p>}
            <div className="action-row compact-actions">
              {(["confirmed", "deferred", "assigned", "dismissed"] as OpenLoopStateValue[]).map((value) => (
                <button key={value} type="button" onClick={() => decide(loop.id, value)}>{value === "confirmed" ? "Confirm" : value === "deferred" ? "Defer" : value === "assigned" ? "Assign" : "Dismiss"}</button>
              ))}
            </div>
            {current.note && <p className="decision-note">RM note · {current.note}</p>}
          </article>
        );
      })}
    </section>
  );
}
