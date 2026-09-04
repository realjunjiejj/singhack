import type { Confidence } from "@/lib/workbench/types";

export function ConfidenceBadge({ confidence, showReasons = false }: { confidence: Confidence; showReasons?: boolean }) {
  return (
    <div className="confidence-block">
      <span className={`badge confidence confidence-${confidence.level.toLowerCase()}`}>
        Confidence {confidence.level} · {confidence.score}
      </span>
      {showReasons && confidence.reasons.length > 0 && (
        <ul className="compact-list muted">
          {confidence.reasons.map((reason) => <li key={reason}>{reason}</li>)}
        </ul>
      )}
    </div>
  );
}
