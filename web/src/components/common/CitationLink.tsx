export function CitationLink({
  evidenceIds,
  onOpen,
}: {
  evidenceIds: string[];
  onOpen: (evidenceId: string) => void;
}) {
  if (evidenceIds.length === 0) return <span className="citation missing-citation">Evidence unavailable</span>;
  return (
    <span className="citation-group" aria-label="Evidence citations">
      {evidenceIds.map((id) => (
        <button key={id} type="button" className="citation" onClick={() => onOpen(id)} aria-label={`Open evidence ${id}`}>
          [{id}]
        </button>
      ))}
    </span>
  );
}
