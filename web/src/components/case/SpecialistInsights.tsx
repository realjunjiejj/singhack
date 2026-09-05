import { CitationLink } from "@/components/common/CitationLink";
import type { AgentReport } from "@/lib/intelligence/types";

const directionLabels: Record<string, string> = {
  "hidden-risk": "Hidden Risk",
  prioritisation: "Prioritisation",
  personalised: "Personalised",
  rebalancing: "Rebalancing",
  "tax-aware": "Tax-aware",
  "life-event": "Life events",
};

export function SpecialistInsights({ caseId, reports, onEvidence }: {
  caseId: string;
  reports: AgentReport[];
  onEvidence: (id: string) => void;
}) {
  const findings = reports
    .filter((report) => report.depth !== "control" && report.agentId !== "dataset-steward")
    .flatMap((report) => report.findings)
    .filter((finding) => finding.caseId === caseId);
  const selected = [
    ...findings.filter((finding) => ["hidden-risk", "prioritisation"].includes(finding.direction)),
    ...findings.filter((finding) => !["hidden-risk", "prioritisation", "explanation"].includes(finding.direction)),
  ];

  if (selected.length === 0) return null;

  return (
    <section className="case-section specialist-insights" aria-labelledby="specialist-insights-title">
      <div className="section-heading">
        <div><p className="eyebrow">Specialist team · evidence bounded</p><h2 id="specialist-insights-title">AI-assisted insights for this client</h2></div>
        <span className="focus-chip">Deep focus: Hidden Risk + Priority</span>
      </div>
      <div className="insight-grid">
        {selected.map((finding) => (
          <article className={`insight-card direction-${finding.direction}`} key={finding.findingId}>
            <header>
              <span>{directionLabels[finding.direction] ?? finding.direction}</span>
              <small className={`narrative-source ${finding.narrativeSource}`}>{finding.narrativeSource === "model-validated" ? "Gemini · evidence validated" : "Deterministic"}</small>
            </header>
            <h3>{finding.title.replace(/\s+[—-]\s+.*$/, "")}</h3>
            <p>{finding.summary}</p>
            <div className="why-it-matters"><strong>Why it matters</strong><span>{finding.whyItMatters}</span></div>
            {finding.limitations[0] && <details><summary>Limits to verify</summary><p>{finding.limitations[0]}</p></details>}
            <CitationLink evidenceIds={finding.evidenceItemIds} onOpen={onEvidence} />
          </article>
        ))}
      </div>
    </section>
  );
}
