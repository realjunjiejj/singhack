import { CitationLink } from "@/components/common/CitationLink";
import type { FactorContribution } from "@/lib/workbench/types";

export function FactorBreakdown({ factors, onEvidence }: { factors: FactorContribution[]; onEvidence?: (id: string) => void }) {
  const maximum = Math.max(1, ...factors.map((factor) => Math.abs(factor.points)));
  return (
    <div className="factor-list" aria-label="Priority factor contributions">
      {factors.map((factor) => (
        <div className="factor" key={`${factor.factor}-${factor.points}`}>
          <div className="factor-heading">
            <span>{factor.factor}</span><strong>+{factor.points} pts</strong>
          </div>
          <div className="factor-track" aria-hidden="true"><span style={{ width: `${Math.max(5, Math.abs(factor.points) / maximum * 100)}%` }} /></div>
          <p>{factor.reason} {onEvidence && <CitationLink evidenceIds={factor.evidenceItemIds} onOpen={onEvidence} />}</p>
        </div>
      ))}
    </div>
  );
}
