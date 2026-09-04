import { CitationLink } from "@/components/common/CitationLink";
import { StatusBadge } from "@/components/common/StatusBadge";
import type { AnticipatorySignal } from "@/lib/workbench/types";

export function SignalList({ signals, onEvidence }: { signals: AnticipatorySignal[]; onEvidence: (id: string) => void }) {
  return (
    <section className="case-section" aria-labelledby="signals-title">
      <p className="relationship-frame">Your client is about to notice this</p>
      <h2 id="signals-title">Anticipatory Signals</h2>
      {signals.length === 0 ? <p className="muted">No Anticipatory Signals supplied for this Client Case.</p> : (
        <div className="card-stack">
          {signals.map((signal) => (
            <article className="signal-card" key={signal.id}>
              <div className="card-topline"><span className="signal-type">{signal.type}</span><StatusBadge status={signal.status} /></div>
              <h3>{signal.summary}</h3>
              <p className="muted">Time horizon · {signal.timeHorizon}</p>
              <CitationLink evidenceIds={signal.evidenceItemIds} onOpen={onEvidence} />
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
