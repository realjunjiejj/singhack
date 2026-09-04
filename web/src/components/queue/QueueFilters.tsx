import type { WorkbenchState } from "@/lib/state/model";
import type { WorkbenchModel } from "@/lib/workbench/types";

function toggle(values: string[], value: string) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export function QueueFilters({
  options,
  filters,
  onChange,
}: {
  options: WorkbenchModel["book"]["filters"];
  filters: WorkbenchState["filters"];
  onChange: (filters: Partial<WorkbenchState["filters"]>) => void;
}) {
  const groups: Array<{ key: keyof Omit<WorkbenchState["filters"], "query">; label: string; values: string[] }> = [
    { key: "signalTypes", label: "Signal", values: options.signalTypes },
    { key: "bookingCentres", label: "Booking", values: options.bookingCentres },
    { key: "urgencyTiers", label: "Urgency", values: options.urgencyTiers },
    { key: "confidenceLevels", label: "Confidence", values: options.confidenceLevels },
  ];
  const activeCount = groups.reduce((count, group) => count + filters[group.key].length, 0);
  return (
    <div className="filters">
      <label className="search-field">
        <span className="sr-only">Search Priority Queue</span>
        <span aria-hidden="true">⌕</span>
        <input value={filters.query} onChange={(event) => onChange({ query: event.target.value })} placeholder="Find a client or issue" />
      </label>
      <details className="filter-panel">
        <summary>Filters {activeCount > 0 && <span className="filter-count">{activeCount}</span>}</summary>
        <div className="filter-groups">
          {groups.map((group) => (
            <fieldset key={group.key}>
              <legend>{group.label}</legend>
              <div className="chip-row">
                {group.values.map((value) => (
                  <label className="check-chip" key={value}>
                    <input
                      type="checkbox"
                      checked={filters[group.key].includes(value)}
                      onChange={() => onChange({ [group.key]: toggle(filters[group.key], value) })}
                    />
                    <span>{value}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
          <button className="text-button" type="button" onClick={() => onChange({ signalTypes: [], bookingCentres: [], urgencyTiers: [], confidenceLevels: [] })}>Clear filters</button>
        </div>
      </details>
    </div>
  );
}
