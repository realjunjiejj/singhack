const demonstrated = [
  "Offline ingestion artifact",
  "Deterministic factors and supplied scenarios",
  "Evidence Packet citations",
  "Cached multilingual drafts",
  "Explicit human approval",
];

const targetControls = [
  "Identity and entitlements",
  "Encryption and secrets management",
  "Persistent audit records",
  "Bounded model gateway",
  "Data residency and monitoring",
  "Deployment segregation",
  "Core-bank and advisory integrations",
];

export function TargetArchitecture() {
  const stages = [
    { number: "01", title: "Governed bank sources", body: "Portfolio, client, relationship and compliance records, plus the Controlled Event Source." },
    { number: "02", title: "Deterministic intelligence", body: "Validated analytics produce stable ranking factors, supplied scenarios and bounded Evidence Packets." },
    { number: "03", title: "Optional language gateway", body: "One Evidence Packet and fixed task at a time; unsupported facts or changed figures are rejected." },
    { number: "04", title: "RM review and approval", body: "Priscilla inspects evidence, edits the Meeting Brief and explicitly approves the current revision." },
    { number: "05", title: "Existing advisory channels", body: "Approved preparation can inform established bank workflows; this prototype does not send or execute." },
  ];
  return (
    <main className="architecture-page">
      <p className="eyebrow">Target architecture · 30-second view</p>
      <h1>Trust is a sequence, not a disclaimer.</h1>
      <p className="architecture-lede">J Buddy keeps calculations deterministic, language bounded, and the Relationship Manager accountable for the conversation.</p>
      <div className="architecture-flow">
        {stages.map((stage, index) => (
          <article key={stage.number}><span>{stage.number}</span><h2>{stage.title}</h2><p>{stage.body}</p>{index < stages.length - 1 && <i aria-hidden="true">→</i>}</article>
        ))}
      </div>
      <div className="architecture-proof">
        <section><p className="eyebrow">Demonstrated now</p><h2>Visible in the prototype</h2><ul>{demonstrated.map((item) => <li key={item}>✓ {item}</li>)}</ul></section>
        <section className="target-controls"><p className="eyebrow">Target controls</p><h2>Required for private-bank deployment</h2><ul>{targetControls.map((item) => <li key={item}>○ {item}</li>)}</ul><p className="boundary-note">These controls are an implementation target. They are not claimed as present in the prototype.</p></section>
      </div>
      <a className="primary-button architecture-back" href="/">← Return to Priscilla’s Client Cases</a>
    </main>
  );
}
