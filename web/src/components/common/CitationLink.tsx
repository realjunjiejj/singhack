"use client";

import { useState } from "react";
import { useEvidenceLabels } from "./EvidenceLabels";

export function CitationLink({ evidenceIds, onOpen }: { evidenceIds: string[]; onOpen: (evidenceId: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const labels = useEvidenceLabels();
  if (evidenceIds.length === 0) return <span className="citation missing-citation">Evidence unavailable</span>;

  const links = (
    <span className="citation-group" aria-label="Evidence citations">
      {evidenceIds.map((id) => (
        <button key={id} type="button" className="citation" onClick={() => onOpen(id)} aria-label={`Open evidence ${id}`} title={`Evidence ID: ${id}`}>
          <span aria-hidden="true">↗</span> {labels[id] ?? "View evidence"}
        </button>
      ))}
    </span>
  );

  if (evidenceIds.length <= 4) return links;
  return (
    <span className="citation-disclosure">
      <button type="button" className="citation-summary" aria-expanded={expanded} onClick={() => setExpanded((current) => !current)}>
        Evidence · {evidenceIds.length} cited records
      </button>
      {expanded ? links : null}
    </span>
  );
}
