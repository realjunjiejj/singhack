import type { ClientCase, WorkbenchModel } from "@/lib/workbench/types";

const coverageItems = [
  {
    title: "Personalised context",
    detail: "Mandate · risk profile · tax position · objectives",
  },
  {
    title: "Portfolio actions",
    detail: "Rebalancing suggestions with the reasoning attached",
  },
  {
    title: "Tax-aware opportunities",
    detail: "Surfaced for RM or specialist review — not tax advice",
  },
  {
    title: "Life-event planning",
    detail: "Retirement · business sale · philanthropy · education · succession",
  },
] as const;

const intelligenceChecks = [
  {
    title: "All portfolios combined",
    detail: "Every portfolio is combined before client-level risk is assessed.",
  },
  {
    title: "Structured-product look-through",
    detail: "Structured products use underlying_reference, not the asset-class label alone.",
  },
  {
    title: "RM-note conflicts stay visible",
    detail: "RM notes and portfolio numbers may conflict; neither is silently preferred.",
  },
  {
    title: "Private-market valuation lag",
    detail: "Private-market reporting lag is treated as context, not automatically as an error.",
  },
] as const;

export function AdvisoryOverview({
  model,
  clientCase,
}: {
  model: WorkbenchModel;
  clientCase: ClientCase;
}) {
  const evidenceCount = new Set(
    model.evidencePackets
      .filter((packet) => packet.caseId === clientCase.caseId)
      .flatMap((packet) => packet.items.map((item) => item.id)),
  ).size;
  const firstSignal = clientCase.anticipatorySignals[0];
  const flow = [
    {
      label: "Portfolio / market signal",
      detail: firstSignal ? `${firstSignal.type} · ${firstSignal.timeHorizon}` : "Client evidence enters the case",
    },
    {
      label: "Relevant change detected",
      detail: `${clientCase.anticipatorySignals.length} supplied signal${clientCase.anticipatorySignals.length === 1 ? "" : "s"} · deterministic Urgency`,
    },
    {
      label: "Client-specific impact",
      detail: "Mandate, risk, tax position, objectives and relationship context",
    },
    {
      label: "Evidence-backed explanation",
      detail: `${evidenceCount} cited record${evidenceCount === 1 ? "" : "s"} · bounded AI language`,
    },
    {
      label: "Potential Advisory Actions",
      detail: `${clientCase.meetingBrief.discussionOptions.length} discussion option${clientCase.meetingBrief.discussionOptions.length === 1 ? "" : "s"} supplied for review`,
    },
    {
      label: "RM reviews insight",
      detail: "Edit, reject, involve a specialist or approve",
    },
    {
      label: "Client conversation",
      detail: "The RM decides what happens next · no automatic send or trade",
    },
  ];

  return (
    <div className="advisory-overview">
      <section className="advisory-flow" aria-labelledby="advisory-flow-title">
        <div className="overview-heading">
          <div>
            <p className="eyebrow">RM-controlled workflow</p>
            <h2 id="advisory-flow-title">From signal to client-ready action</h2>
          </div>
          <span className="control-seal">RM decides</span>
        </div>
        <p className="overview-intro">Move from insight to client action. The Relationship Manager stays in control.</p>
        <ol className="advisory-path">
          {flow.map((step, index) => (
            <li key={step.label}>
              <span className="path-index" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
              <div><strong>{step.label}</strong><small>{step.detail}</small></div>
            </li>
          ))}
        </ol>
      </section>

      <section className="overview-group" aria-labelledby="coverage-title">
        <div className="overview-group-heading">
          <p className="eyebrow">Advisory coverage</p>
          <h3 id="coverage-title">What the workbench brings together</h3>
        </div>
        <ul className="coverage-list">
          {coverageItems.map((item) => (
            <li key={item.title}><strong>{item.title}</strong><span>{item.detail}</span></li>
          ))}
          <li className="coverage-priority">
            <strong>Whole-Book priority</strong>
            <span>{model.book.clientCount} clients · {model.book.portfolioCount} portfolios · stable deterministic order</span>
          </li>
        </ul>
      </section>

      <section className="overview-group" aria-labelledby="intelligence-checks-title">
        <div className="overview-group-heading">
          <p className="eyebrow">Things worth knowing</p>
          <h3 id="intelligence-checks-title">How the intelligence reads the data</h3>
        </div>
        <ul className="intelligence-checks">
          {intelligenceChecks.map((item) => (
            <li key={item.title}><span aria-hidden="true">✓</span><div><strong>{item.title}</strong><small>{item.detail}</small></div></li>
          ))}
          <li>
            <span aria-hidden="true">✓</span>
            <div>
              <strong>Real-world imperfections</strong>
              <small>Data quality: {model.meta.dataQuality.status} · {model.meta.dataQuality.issues.length} issue{model.meta.dataQuality.issues.length === 1 ? "" : "s"} recorded; Confidence remains separate from Urgency.</small>
            </div>
          </li>
        </ul>
      </section>
    </div>
  );
}
