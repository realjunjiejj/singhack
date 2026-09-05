import { CitationLink } from "@/components/common/CitationLink";
import type { WorkbenchState } from "@/lib/state/model";
import { formatDate, sentenceCase } from "@/lib/workbench/format";
import type { ClientCase } from "@/lib/workbench/types";

export function ClientPulse({
  clientCase,
  openLoopStates,
  onEvidence,
}: {
  clientCase: ClientCase;
  openLoopStates: WorkbenchState["openLoopStates"];
  onEvidence: (id: string) => void;
}) {
  const portfolioSignal = clientCase.anticipatorySignals.find((signal) =>
    /(CREDIT|MANDATE|SUITABILITY|CONCENTRATION|LIQUIDITY)/.test(signal.id),
  ) ?? clientCase.anticipatorySignals[0];
  const leadLoop = clientCase.openLoops[0];
  const leadClock = [...clientCase.governanceClocks].sort((left, right) => left.daysRemaining - right.daysRemaining)[0];
  const datedSignal = clientCase.anticipatorySignals
    .filter((signal) => signal.id.includes("CASH_NEED"))
    .map((signal) => ({ signal, daysRemaining: Number.parseInt(signal.timeHorizon, 10) }))
    .filter((item) => Number.isFinite(item.daysRemaining))
    .sort((left, right) => left.daysRemaining - right.daysRemaining)[0];
  const nextDate = datedSignal && (!leadClock || datedSignal.daysRemaining < leadClock.daysRemaining)
    ? {
        daysRemaining: datedSignal.daysRemaining,
        summary: datedSignal.signal.summary,
        evidenceItemIds: datedSignal.signal.evidenceItemIds,
      }
    : leadClock
      ? {
          daysRemaining: leadClock.daysRemaining,
          summary: `${leadClock.summary} Due ${formatDate(leadClock.dueDate)}.`,
          evidenceItemIds: leadClock.evidenceItemIds,
        }
      : null;
  const loopState = leadLoop ? openLoopStates[leadLoop.id]?.state ?? leadLoop.state : null;

  return (
    <section className="case-section client-pulse" aria-labelledby="client-pulse-title">
      <div className="pulse-heading">
        <div><p className="eyebrow">At a glance</p><h2 id="client-pulse-title">Client pulse</h2></div>
        <p>What changed, what is waiting, and what has a date.</p>
      </div>

      <div className="pulse-list">
        <article className="pulse-row pulse-now">
          <span className="pulse-dot" aria-hidden="true" />
          <div className="pulse-copy">
            <div className="pulse-label"><strong>Portfolio</strong><span>{portfolioSignal ? sentenceCase(portfolioSignal.status) : "Clear"}</span></div>
            <p>{portfolioSignal?.summary ?? "No portfolio-level Anticipatory Signal was supplied."}</p>
            {portfolioSignal && <CitationLink evidenceIds={portfolioSignal.evidenceItemIds} onOpen={onEvidence} />}
          </div>
        </article>

        <article className="pulse-row pulse-relationship">
          <span className="pulse-dot" aria-hidden="true" />
          <div className="pulse-copy">
            <div className="pulse-label"><strong>Relationship</strong><span>{loopState ? sentenceCase(loopState) : "Clear"}</span></div>
            <p>{leadLoop?.summary ?? "No unanswered client thread was supplied."}</p>
            {leadLoop && <CitationLink evidenceIds={leadLoop.evidenceItemIds} onOpen={onEvidence} />}
          </div>
        </article>

        <article className="pulse-row pulse-deadline">
          <span className="pulse-dot" aria-hidden="true" />
          <div className="pulse-copy">
            <div className="pulse-label">
              <strong>Next date</strong>
              <span>{nextDate ? `${nextDate.daysRemaining < 0 ? Math.abs(nextDate.daysRemaining) + " days overdue" : nextDate.daysRemaining + " days"}` : "None"}</span>
            </div>
            <p>{nextDate?.summary ?? "No dated client need or Governance Clock was supplied."}</p>
            {nextDate && <CitationLink evidenceIds={nextDate.evidenceItemIds} onOpen={onEvidence} />}
          </div>
        </article>
      </div>
    </section>
  );
}
