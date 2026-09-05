import { CitationLink } from "@/components/common/CitationLink";
import { formatMoney } from "@/lib/workbench/format";
import type { ClientCase, EvidencePacket } from "@/lib/workbench/types";
import { PortfolioTrend } from "./PortfolioTrend";

const lensLinks = [
  { number: "01", label: "Whole Book", target: "priority-queue" },
  { number: "02", label: "Personalise", target: "personalised-guidance" },
  { number: "03", label: "Rebalance", target: "portfolio-position" },
  { number: "04", label: "Tax-aware", target: "tax-planning" },
  { number: "05", label: "Life events", target: "life-events" },
];

function goTo(target: string) {
  const element = document.getElementById(target);
  element?.scrollIntoView({ behavior: "smooth", block: "start" });
  element?.focus({ preventScroll: true });
}

export function AdvisoryOverview({ clientCase, evidencePackets, onEvidence, onPrepare, onWhatIf }: {
  clientCase: ClientCase;
  evidencePackets: EvidencePacket[];
  onEvidence: (id: string) => void;
  onPrepare: () => void;
  onWhatIf: () => void;
}) {
  const allEvidence = Array.from(new Set(clientCase.meetingBrief.evidenceItemIds));
  const firstMetric = Array.from(new Set(clientCase.timeline.flatMap((point) => Object.keys(point.metrics))))[0];
  const taxSignals = clientCase.anticipatorySignals.filter((signal) => signal.type === "tax-aware");
  const lifeSignals = clientCase.anticipatorySignals.filter((signal) => signal.type === "life-event");
  const taxClocks = clientCase.governanceClocks.filter((clock) => clock.type.toLowerCase().includes("tax"));
  const trigger = firstMetric?.toLowerCase() === "ltv" ? clientCase.collateralStressTest?.scenarios[0]?.triggerPct : undefined;
  const basePosition = clientCase.collateralStressTest?.scenarios.find((scenario) => scenario.collateralChangePct === 0);

  return (
    <>
      <nav className="advisory-lenses" aria-label="Five RM outcomes">
        {lensLinks.map((lens) => <button type="button" key={lens.target} onClick={() => goTo(lens.target)}><span>{lens.number}</span>{lens.label}</button>)}
      </nav>

      <section className="decision-card" id="personalised-guidance" tabIndex={-1} aria-labelledby="personalised-title">
        <div className="decision-card-heading">
          <div><p className="eyebrow">AI-assisted synthesis · evidence grounded</p><h2 id="personalised-title">Recommended conversation strategy</h2></div>
          <span className="human-control">RM decides</span>
        </div>
        <p className="opening-prompt">“{clientCase.meetingBrief.openingQuestion}”</p>
        <div className="strategy-grid">
          <div><span className="section-kicker">Why this is personal</span><p>{clientCase.meetingBrief.whyItMatters}</p></div>
          <div>
            <span className="section-kicker">Explore with the client</span>
            <ol>{clientCase.meetingBrief.discussionOptions.slice(0, 3).map((option) => <li key={option}>{option}</li>)}</ol>
          </div>
          <div>
            <span className="section-kicker">Verify before advising</span>
            {clientCase.meetingBrief.uncertainties.length > 0 ? <ul>{clientCase.meetingBrief.uncertainties.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul> : <p>No material uncertainty supplied.</p>}
          </div>
        </div>
        <div className="decision-actions">
          <button type="button" className="primary-button" onClick={onPrepare}>Prepare Meeting Brief</button>
          <CitationLink evidenceIds={allEvidence} onOpen={onEvidence} />
        </div>
        <p className="boundary-note">This synthesis organises supplied Evidence Packets and approved Guided Actions. It does not place trades or replace suitability, tax, or specialist review.</p>
      </section>

      <section className="case-section portfolio-section" id="portfolio-position" tabIndex={-1} aria-labelledby="portfolio-title">
        <div className="section-heading">
          <div><p className="eyebrow">See the change</p><h2 id="portfolio-title">Position changes &amp; rebalancing lens</h2></div>
          {clientCase.collateralStressTest && <button type="button" className="text-button" onClick={onWhatIf}>View supplied what-if</button>}
        </div>
        {firstMetric ? <PortfolioTrend timeline={clientCase.timeline} metric={firstMetric} trigger={trigger} onEvidence={onEvidence} /> : <p className="muted">No supplied timeline metric is available.</p>}
        {basePosition && <PositionStructure scenario={basePosition} />}
        <AssetAllocation evidencePackets={evidencePackets} onEvidence={onEvidence} />
      </section>

      <div className="planning-grid">
        <section className="planning-card" id="tax-planning" tabIndex={-1} aria-labelledby="tax-title">
          <span className="lens-number">04</span><p className="eyebrow">Tax-aware optimisation</p><h2 id="tax-title">Tax planning checkpoint</h2>
          {taxSignals.length + taxClocks.length > 0 ? <ul>{taxSignals.map((signal) => <li key={signal.id}>{signal.summary}</li>)}{taxClocks.map((clock) => <li key={clock.id}>{clock.summary}</li>)}</ul> : <p>No tax-specific opportunity is supplied for this Client Case. Confirm jurisdiction and advice scope before recommending action.</p>}
          <p className="planning-status">{taxSignals.length + taxClocks.length > 0 ? "Review supplied tax signal" : "Specialist verification required"}</p>
        </section>
        <section className="planning-card" id="life-events" tabIndex={-1} aria-labelledby="life-title">
          <span className="lens-number">05</span><p className="eyebrow">Life-event wealth planning</p><h2 id="life-title">Objectives, obligations &amp; relationship memory</h2>
          <p>{lifeSignals[0]?.summary ?? clientCase.whyNow}</p>
          <div className="planning-counts"><span><strong>{clientCase.anticipatorySignals.length}</strong> signals</span><span><strong>{clientCase.openLoops.length}</strong> open loops</span><span><strong>{clientCase.governanceClocks.length}</strong> clocks</span></div>
        </section>
      </div>
    </>
  );
}

function AssetAllocation({ evidencePackets, onEvidence }: { evidencePackets: EvidencePacket[]; onEvidence: (id: string) => void }) {
  const snapshots = evidencePackets
    .filter((packet) => packet.signalType === "explanation")
    .flatMap((packet) => packet.items)
    .map((item) => ({ item, value: allocationValue(item.value) }))
    .filter((entry): entry is { item: EvidencePacket["items"][number]; value: AllocationValue } => entry.value !== null)
    .sort((a, b) => a.value.snapshotDate.localeCompare(b.value.snapshotDate));
  const latest = snapshots.at(-1);

  if (!latest) {
    return <div className="allocation-notice"><strong>Asset allocation not supplied</strong><span>No percentages are inferred. Upload data through the current engine to include source-backed asset-class weights.</span></div>;
  }
  const allocations = Object.entries(latest.value.byAssetClassPct).sort((a, b) => b[1] - a[1]);
  return (
    <div className="asset-allocation">
      <div className="chart-heading"><div><span className="section-kicker">Latest supplied snapshot</span><h3>Portfolio allocation by asset class</h3></div><small>{latest.value.snapshotDate}</small></div>
      <div className="allocation-bars" role="img" aria-label={`Portfolio allocation: ${allocations.map(([name, value]) => `${name} ${value.toFixed(1)}%`).join(", ")}`}>
        {allocations.map(([name, value]) => <div className="allocation-row" key={name}><div><span>{name}</span><strong>{value.toFixed(1)}%</strong></div><div className="allocation-track"><span style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></div></div>)}
      </div>
      <CitationLink evidenceIds={[latest.item.id]} onOpen={onEvidence} />
      <p className="boundary-note">Percentages are supplied by the deterministic analysis engine; the browser only displays them.</p>
    </div>
  );
}

type AllocationValue = { snapshotDate: string; byAssetClassPct: Record<string, number> };

function allocationValue(value: unknown): AllocationValue | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as { snapshotDate?: unknown; byAssetClassPct?: unknown };
  if (typeof candidate.snapshotDate !== "string" || !candidate.byAssetClassPct || typeof candidate.byAssetClassPct !== "object") return null;
  const entries = Object.entries(candidate.byAssetClassPct);
  if (entries.length === 0 || entries.some(([, amount]) => typeof amount !== "number" || !Number.isFinite(amount))) return null;
  return { snapshotDate: candidate.snapshotDate, byAssetClassPct: Object.fromEntries(entries) as Record<string, number> };
}

function PositionStructure({ scenario }: { scenario: NonNullable<ClientCase["collateralStressTest"]>["scenarios"][number] }) {
  const rows = [
    { label: "Collateral market value", money: scenario.collateralValue },
    { label: "Eligible lending value", money: scenario.lendingValue },
    { label: "Drawn amount", money: scenario.drawnAmount },
  ];
  const maximum = Math.max(...rows.map((row) => row.money.amount));

  return (
    <div className="position-structure" role="img" aria-label={`Current lending position. ${rows.map((row) => `${row.label}: ${formatMoney(row.money)}`).join(", ")}`}>
      <div className="chart-heading"><div><span className="section-kicker">Current supplied values</span><h3>Lending position structure</h3></div></div>
      {rows.map((row, index) => (
        <div className="position-row" key={row.label}>
          <div><span>{row.label}</span><strong>{formatMoney(row.money)}</strong></div>
          <div className="position-track"><span className={`position-bar bar-${index + 1}`} style={{ width: `${(row.money.amount / maximum) * 100}%` }} /></div>
        </div>
      ))}
      <p className="boundary-note">Bar lengths compare supplied monetary values on the same currency scale; they are not portfolio allocation weights.</p>
    </div>
  );
}
