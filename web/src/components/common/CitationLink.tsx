"use client";

import { useState } from "react";

export function CitationLink({
  evidenceIds,
  onOpen,
}: {
  evidenceIds: string[];
  onOpen: (evidenceId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  if (evidenceIds.length === 0) return <span className="citation missing-citation">Evidence unavailable</span>;
  const links = (
    <span className="citation-group" aria-label="Evidence citations">
      {evidenceIds.map((id, index) => (
        <button key={id} type="button" className="citation" onClick={() => onOpen(id)} aria-label={`Open evidence ${id}`} title={id}>
          Evidence {index + 1}
        </button>
      ))}
    </span>
  );
  if (evidenceIds.length <= 4) return links;
  return (
    <span className="citation-disclosure">
      <button
        type="button"
        className="citation-summary"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
      >
        Evidence · {evidenceIds.length} cited records
      </button>
      {expanded ? links : null}
    </span>
  );
}
