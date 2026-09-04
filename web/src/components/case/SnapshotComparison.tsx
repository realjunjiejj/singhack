import { CitationLink } from "@/components/common/CitationLink";
import { formatDate, formatMeasure } from "@/lib/workbench/format";
import type { TimelinePoint } from "@/lib/workbench/types";

export function SnapshotComparison({
  timeline,
  selected,
  onSelect,
  onEvidence,
}: {
  timeline: TimelinePoint[];
  selected: [string, string];
  onSelect: (value: [string, string]) => void;
  onEvidence: (id: string) => void;
}) {
  const points = selected.map((date) => timeline.find((point) => point.date === date)).filter(Boolean) as TimelinePoint[];
  const metricNames = Array.from(new Set(points.flatMap((point) => Object.keys(point.metrics))));
  return (
    <section className="case-section" aria-labelledby="timeline-title">
      <div className="section-heading"><div><p className="eyebrow">Five-snapshot record</p><h2 id="timeline-title">What changed</h2></div></div>
      <div className="timeline-strip" aria-label="Available snapshots">
        {timeline.map((point) => <span key={point.date} className={selected.includes(point.date) ? "selected" : ""}><i />{formatDate(point.date)}</span>)}
      </div>
      <div className="compare-selects">
        {[0, 1].map((index) => (
          <label key={index}>Snapshot {index + 1}
            <select value={selected[index]} onChange={(event) => {
              const next: [string, string] = [...selected];
              next[index] = event.target.value;
              onSelect(next);
            }}>
              {timeline.map((point) => <option value={point.date} key={point.date}>{formatDate(point.date)} · {point.label}</option>)}
            </select>
          </label>
        ))}
      </div>
      <div className="comparison-grid">
        {points.map((point) => (
          <article key={point.date}>
            <time>{formatDate(point.date)}</time><h3>{point.label}</h3>
            <dl>{metricNames.map((metric) => point.metrics[metric] && <div key={metric}><dt>{metric}</dt><dd>{formatMeasure(point.metrics[metric])}</dd></div>)}</dl>
            <CitationLink evidenceIds={point.evidenceItemIds} onOpen={onEvidence} />
          </article>
        ))}
      </div>
      <p className="boundary-note">Comparison shows supplied metrics only. No return attribution is calculated in the browser.</p>
    </section>
  );
}
