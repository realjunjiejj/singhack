import { CitationLink } from "@/components/common/CitationLink";
import { StateBadge } from "@/components/common/StatusBadge";
import { formatDate } from "@/lib/workbench/format";
import type { GovernanceClock } from "@/lib/workbench/types";

export function GovernanceClocks({ clocks, onEvidence }: { clocks: GovernanceClock[]; onEvidence: (id: string) => void }) {
  return (
    <section className="case-section" aria-labelledby="governance-title">
      <h2 id="governance-title">Governance Clocks</h2>
      {clocks.length === 0 ? <p className="muted">No active Governance Clocks supplied.</p> : (
        <div className="card-stack">
          {clocks.map((clock) => (
            <article className="governance-card" key={clock.id}>
              <div className="clock-number">{clock.daysRemaining}</div>
              <div>
                <div className="card-topline"><StateBadge value={clock.status} /><span>{clock.type}</span></div>
                <h3>{clock.summary}</h3>
                <p>Due {formatDate(clock.dueDate)} · {clock.daysRemaining < 0 ? `${Math.abs(clock.daysRemaining)} days overdue` : clock.daysRemaining === 0 ? "due today" : `${clock.daysRemaining} days remaining`}</p>
                <CitationLink evidenceIds={clock.evidenceItemIds} onOpen={onEvidence} />
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
