import { CitationLink } from "@/components/common/CitationLink";
import { formatDate, formatMeasure } from "@/lib/workbench/format";
import type { TimelinePoint } from "@/lib/workbench/types";

function metricLabel(metric: string) {
  return metric
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/_/g, " ")
    .replace(/^ltv$/i, "LTV")
    .replace(/^./, (character) => character.toUpperCase());
}

export function PortfolioTrend({ timeline, metric, trigger, onEvidence }: {
  timeline: TimelinePoint[];
  metric: string;
  trigger?: number;
  onEvidence: (id: string) => void;
}) {
  const points = timeline
    .map((point) => ({ point, measure: point.metrics[metric] }))
    .filter((entry) => entry.measure !== undefined);

  if (points.length === 0) return <p className="muted">No supplied position history is available for this lens.</p>;

  const width = 620;
  const height = 210;
  const paddingX = 52;
  const paddingY = 30;
  const values = points.map(({ measure }) => measure.value);
  const scaleValues = trigger === undefined ? values : [...values, trigger];
  const minimum = Math.min(...scaleValues);
  const maximum = Math.max(...scaleValues);
  const range = maximum - minimum || 1;
  const chartHeight = height - paddingY * 2;
  const chartWidth = width - paddingX * 2;
  const xFor = (index: number) => paddingX + (points.length === 1 ? chartWidth / 2 : (index / (points.length - 1)) * chartWidth);
  const yFor = (value: number) => paddingY + ((maximum - value) / range) * chartHeight;
  const polyline = points.map(({ measure }, index) => `${xFor(index)},${yFor(measure.value)}`).join(" ");
  const description = points.map(({ point, measure }) => `${formatDate(point.date)} ${formatMeasure(measure)}`).join(", ");

  return (
    <div className="portfolio-trend">
      <div className="chart-heading">
        <div><span className="section-kicker">Supplied metric history</span><h3>{metricLabel(metric)} position</h3></div>
        <div><small>Latest supplied</small><strong>{formatMeasure(points.at(-1)!.measure)}</strong></div>
      </div>
      <svg className="trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${metricLabel(metric)} trend. ${description}`}>
        <line className="chart-grid-line" x1={paddingX} x2={width - paddingX} y1={paddingY} y2={paddingY} />
        <line className="chart-grid-line" x1={paddingX} x2={width - paddingX} y1={height - paddingY} y2={height - paddingY} />
        {trigger !== undefined && (
          <g className="trigger-line">
            <line x1={paddingX} x2={width - paddingX} y1={yFor(trigger)} y2={yFor(trigger)} />
            <text x={width - paddingX} y={yFor(trigger) - 7} textAnchor="end">{trigger}% trigger</text>
          </g>
        )}
        <polyline className="trend-line" points={polyline} />
        {points.map(({ point, measure }, index) => (
          <g className="trend-point" key={point.date}>
            <circle cx={xFor(index)} cy={yFor(measure.value)} r="6" />
            <text className="trend-value" x={xFor(index)} y={yFor(measure.value) - 13} textAnchor="middle">{formatMeasure(measure)}</text>
            <text className="trend-date" x={xFor(index)} y={height - 8} textAnchor="middle">{formatDate(point.date)}</text>
          </g>
        ))}
      </svg>
      <div className="chart-event-list" aria-label={`${metricLabel(metric)} timeline details`}>
        {points.map(({ point, measure }) => (
          <div key={point.date}>
            <span><i aria-hidden="true" />{point.label}</span>
            <strong>{formatMeasure(measure)}</strong>
            <CitationLink evidenceIds={point.evidenceItemIds} onOpen={onEvidence} />
          </div>
        ))}
      </div>
    </div>
  );
}
