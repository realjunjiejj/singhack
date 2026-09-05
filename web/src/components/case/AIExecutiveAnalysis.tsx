import { CitationLink } from "@/components/common/CitationLink";
import { getExecutiveInsight } from "@/lib/intelligence/executiveAnalysis";
import type { ClientCase } from "@/lib/workbench/types";

export function AIExecutiveAnalysis({
  clientCase,
  onEvidence,
  onPrepare,
}: {
  clientCase: ClientCase;
  onEvidence: (id: string) => void;
  onPrepare: () => void;
}) {
  const insight = getExecutiveInsight(clientCase);
  const evidenceIds = Array.from(
    new Set([
      ...clientCase.facts.flatMap((f) => f.evidenceItemIds),
      ...clientCase.anticipatorySignals.flatMap((s) => s.evidenceItemIds),
      ...clientCase.meetingBrief.evidenceItemIds,
    ]),
  ).slice(0, 8);

  return (
    <section className="case-section ai-executive-analysis" aria-labelledby="ai-exec-title">
      <div className="executive-analysis-header">
        <div className="header-meta-row">
          <span className="executive-pill">ACTUAL INTELLIGENCE · DEEP CLIENT ADVISORY</span>
          <span className="rm-badge">RM Decides · Evidence Grounded</span>
        </div>
        <h2 id="ai-exec-title">{insight.headline}</h2>
        <p className="executive-subtitle">
          Holistic synthesis of life stage, cashflow requirements, portfolio drawdowns, and client behavioral constraints.
        </p>
      </div>

      <div className="executive-analysis-grid">
        {/* Pillar 01: What Happened */}
        <article className="exec-card card-happened">
          <div className="card-kicker">
            <span className="step-num">01</span>
            <span className="step-title">WHAT HAPPENED</span>
          </div>
          <h3>Macro Shocks &amp; Portfolio Reality</h3>
          <p className="card-body-text">{insight.whatHappened.summary}</p>
          <div className="metric-chip-row">
            {insight.whatHappened.metrics.map((m) => (
              <div key={m.label} className="metric-chip">
                <span className="chip-value">{m.value}</span>
                <span className="chip-label">{m.label}</span>
              </div>
            ))}
          </div>
        </article>

        {/* Pillar 02: The Real Dilemma / Tension */}
        <article className="exec-card card-dilemma">
          <div className="card-kicker">
            <span className="step-num">02</span>
            <span className="step-title">THE CLIENT DILEMMA</span>
          </div>
          <h3>Behavioral Belief vs. Structural Reality</h3>
          <p className="card-body-text">{insight.clientDilemma.tension}</p>
          <div className="trap-callout">
            <strong className="trap-header">⚠️ The Structural Trap:</strong>
            <p>{insight.clientDilemma.trapSummary}</p>
          </div>
        </article>

        {/* Pillar 03: What Should Be Done */}
        <article className="exec-card card-action">
          <div className="card-kicker">
            <span className="step-num">03</span>
            <span className="step-title">WHAT SHOULD BE DONE</span>
          </div>
          <h3>Actionable RM Strategy</h3>
          <ol className="action-step-list">
            {insight.whatShouldBeDone.map((step, idx) => (
              <li key={idx}>
                <strong>{step.title}</strong>
                <p>{step.detail}</p>
              </li>
            ))}
          </ol>
        </article>

        {/* Pillar 04: How We Open That Conversation */}
        <article className="exec-card card-conversation">
          <div className="card-kicker">
            <span className="step-num">04</span>
            <span className="step-title">HOW TO OPEN THE CONVERSATION</span>
          </div>
          <h3>Client-Ready Empathetic Script</h3>
          <blockquote className="client-quote-block">
            {insight.conversationScript.opener}
          </blockquote>
          <div className="why-works-box">
            <strong>Why this proves we understand the client:</strong>
            <p>{insight.conversationScript.whyItWorks}</p>
          </div>
          <div className="exec-card-actions">
            <button type="button" className="primary-button" onClick={onPrepare}>
              Prepare Meeting Brief
            </button>
            <CitationLink evidenceIds={evidenceIds} onOpen={onEvidence} />
          </div>
        </article>
      </div>
    </section>
  );
}
