import { useEffect } from "react";
import { CitationLink } from "@/components/common/CitationLink";
import { formatEvidenceValue, formatMeasure, formatDate } from "@/lib/workbench/format";
import type { EvidencePacket } from "@/lib/workbench/types";

export function EvidenceChain({
  packets,
  activeEvidenceItemId,
  onEvidence,
  onBack,
}: {
  packets: EvidencePacket[];
  activeEvidenceItemId: string | null;
  onEvidence: (id: string) => void;
  onBack: () => void;
}) {
  useEffect(() => {
    if (!activeEvidenceItemId) return;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.getElementById(`evidence-${activeEvidenceItemId}`)?.scrollIntoView({ block: "center", behavior: reducedMotion ? "auto" : "smooth" });
  }, [activeEvidenceItemId]);

  return (
    <div className="surface-content evidence-chain">
      <div className="evidence-path" aria-label="Evidence Chain stages">
        {[
          "Source record",
          "Exact value",
          "Derived metric",
          "Interpretation",
          "Advisory significance",
        ].map((stage, index) => <span key={stage}><i>{index + 1}</i>{stage}</span>)}
      </div>
      <button className="text-button back-link" type="button" onClick={onBack}>← Back to claim</button>
      {packets.length === 0 ? <p className="muted">No Evidence Packet was supplied for this Client Case.</p> : packets.map((packet) => (
        <section className="packet" key={packet.packetId} aria-labelledby={`packet-${packet.packetId}`}>
          <div className="packet-header">
            <div><p className="eyebrow">{packet.signalType} · {packet.status}</p><h3 id={`packet-${packet.packetId}`}>{packet.packetId}</h3></div>
            <time>{formatDate(packet.asOfDate)}</time>
          </div>
          <div className="evidence-items">
            {packet.items.map((item) => (
              <article id={`evidence-${item.id}`} className={`evidence-item ${activeEvidenceItemId === item.id ? "is-focused" : ""}`} key={item.id} tabIndex={-1}>
                <div className="card-topline"><span className="evidence-id">{item.id}</span><span>Fact</span></div>
                <h4>{item.label}</h4>
                <p className="evidence-value">{formatEvidenceValue(item.value)}</p>
                <dl className="source-record">
                  <div><dt>Source</dt><dd>{item.sourceReference.file.split(/[\\/]/).pop()}</dd></div>
                  <div><dt>Record</dt><dd>{item.sourceReference.recordKey}</dd></div>
                  {item.sourceReference.field && <div><dt>Field</dt><dd>{item.sourceReference.field}</dd></div>}
                </dl>
              </article>
            ))}
          </div>
          {packet.derivedMetrics.length > 0 && (
            <div className="metric-list">
              <h4>Derived metrics</h4>
              {packet.derivedMetrics.map((metric) => (
                <article id={`evidence-${metric.id}`} className={`derived-metric ${activeEvidenceItemId === metric.id ? "is-focused" : ""}`} key={metric.id} tabIndex={-1}>
                  <div className="card-topline"><strong>{metric.name}</strong><span>{metric.id}</span></div>
                  <p className="metric-result">{formatMeasure(metric.result)}</p>
                  <dl>
                    <div><dt>Formula</dt><dd>{metric.formula}</dd></div>
                    <div><dt>Inputs</dt><dd>{formatEvidenceValue(metric.inputs)}</dd></div>
                    <div><dt>Snapshot</dt><dd>{formatDate(metric.snapshotDate)}</dd></div>
                    <div><dt>Unrounded result</dt><dd>{metric.result.value}</dd></div>
                  </dl>
                </article>
              ))}
            </div>
          )}
          {(["facts", "interpretations", "assumptions", "uncertainties", "conflicts"] as const).map((kind) => packet[kind].length > 0 && (
            <div className={`packet-claims ${kind}`} key={kind}>
              <h4>{kind === "conflicts" ? "Evidence Conflicts" : kind}</h4>
              {packet[kind].map((claim) => <p key={claim.id}>{claim.statement} <CitationLink evidenceIds={claim.evidenceItemIds} onOpen={onEvidence} /></p>)}
              {kind === "conflicts" && <p className="boundary-note">Both source values remain visible. The conflict reduces Confidence; the workbench does not reconcile it.</p>}
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
