import { Fragment } from "react";
import { EmptyState } from "@/components/common/EmptyState";
import type { WorkbenchState } from "@/lib/state/model";
import { filterPriorityQueue } from "@/lib/state/selectors";
import type { WorkbenchModel } from "@/lib/workbench/types";
import { selectFeaturedCases } from "@/lib/workbench/featuredCases";
import { QueueFilters } from "./QueueFilters";
import { QueueItem } from "./QueueItem";

export function PriorityQueue({
  model,
  state,
  onFilters,
  onSelect,
  onEvidence,
}: {
  model: WorkbenchModel;
  state: WorkbenchState;
  onFilters: (filters: Partial<WorkbenchState["filters"]>) => void;
  onSelect: (caseId: string) => void;
  onEvidence: (caseId: string, evidenceId: string) => void;
}) {
  const visible = filterPriorityQueue(model.book.priorityQueue, state.filters, model.clientCases);
  const featured = selectFeaturedCases(model.book.priorityQueue);

  return (
    <aside className="queue-column" id="priority-queue" tabIndex={-1} aria-labelledby="queue-title">
      <div className="column-header queue-header">
        <div><p className="eyebrow">Choose</p><h1 id="queue-title">Priority Queue</h1></div>
        <span className="row-count">{visible.length}/{model.book.priorityQueue.length}</span>
      </div>
      <p className="queue-explainer">Ordered by deterministic Urgency. Confidence is evidence quality, not priority.</p>
      {featured.cases.length > 0 && (
        <div className="demo-finds" aria-label={featured.heading}>
          <span>{featured.heading}</span>
          <div className="chip-row">
            {featured.cases.map((entry) => {
              const isActive = state.activeCaseId === entry.caseId;
              return (
                <button
                  key={entry.clientId}
                  type="button"
                  className={isActive ? "active" : undefined}
                  onClick={() => onSelect(entry.caseId)}
                >
                  {entry.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
      <QueueFilters options={model.book.filters} filters={state.filters} onChange={onFilters} />
      <div className="queue-list">
        {visible.length === 0 ? (
          <EmptyState title="No Client Cases match" body="Clear one or more filters to restore the artifact’s stable order." />
        ) : visible.map((item, index) => (
          <Fragment key={item.caseId}>
            {(index === 0 || visible[index - 1]?.urgency.tier !== item.urgency.tier) && <div className="tier-divider">{item.urgency.tier} Urgency</div>}
            <QueueItem item={item} active={state.activeCaseId === item.caseId} onSelect={() => onSelect(item.caseId)} onEvidence={(evidenceId) => onEvidence(item.caseId, evidenceId)} />
          </Fragment>
        ))}
      </div>
    </aside>
  );
}
