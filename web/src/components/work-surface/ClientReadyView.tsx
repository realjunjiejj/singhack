import { CitationLink } from "@/components/common/CitationLink";
import type { MeetingBriefState } from "@/lib/state/model";
import type { ClientCase, ClientReadyDraft } from "@/lib/workbench/types";

function canonicalText(clientCase: ClientCase, brief?: MeetingBriefState) {
  const source = brief?.fields ?? clientCase.meetingBrief;
  return [source.whatChanged, source.whyItMatters, source.openingQuestion, ...source.discussionOptions].join("\n\n");
}

export function ClientReadyView({
  clientCase,
  brief,
  onEvidence,
}: {
  clientCase: ClientCase;
  brief?: MeetingBriefState;
  onEvidence: (id: string) => void;
}) {
  const drafts = clientCase.clientReadyDrafts ?? [];
  const translated = drafts.find((draft) => draft.language !== draft.canonicalLanguage) ?? drafts[0];
  const canonicalDraft = drafts.find((draft) => draft.language === draft.canonicalLanguage);
  const canonical = canonicalDraft?.content ?? canonicalText(clientCase, brief);
  const citations = translated?.evidenceItemIds ?? canonicalDraft?.evidenceItemIds ?? clientCase.meetingBrief.evidenceItemIds;
  return (
    <div className="surface-content client-ready">
      <div className="brief-status draft"><span>Client-Ready View · review draft</span><strong>Cached / offline mode</strong></div>
      <p className="boundary-note">Canonical and reporting-language content are supplied by the artifact. No browser translation or regeneration is used, and nothing can be sent from this view.</p>
      {!translated ? <p className="muted">No cached Client-Ready draft was supplied for this case. Optional live language is unavailable offline.</p> : (
        <div className="bilingual-grid">
          <DraftPanel title={`Canonical · ${translated.canonicalLanguage}`} content={canonical} status={brief?.status === "approved" ? `RM-approved revision ${brief.revision}` : "Draft"} citations={citations} onEvidence={onEvidence} />
          <DraftPanel title={`Client reporting language · ${translated.language}`} content={translated.content} status="Draft · RM review required" citations={citations} onEvidence={onEvidence} />
        </div>
      )}
      <div className="guardrail-banner">Optional live language unavailable · validated cached content remains available</div>
    </div>
  );
}

function languageCode(title: string) {
  if (title.includes("Traditional Chinese")) return "zh-Hant";
  if (title.includes("German")) return "de";
  return "en";
}

function DraftPanel({ title, content, status, citations, onEvidence }: { title: string; content: string; status: string; citations: string[]; onEvidence: (id: string) => void }) {
  return (
    <article className="draft-panel" lang={languageCode(title)}>
      <div className="card-topline"><h3>{title}</h3><span>{status}</span></div>
      <p className="draft-copy">{content}</p>
      <CitationLink evidenceIds={citations} onOpen={onEvidence} />
    </article>
  );
}
