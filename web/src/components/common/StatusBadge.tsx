import { sentenceCase, statusLabels } from "@/lib/workbench/format";
import type { CaseStatus, UrgencyTier } from "@/lib/workbench/types";

export function StatusBadge({ status }: { status: CaseStatus }) {
  return <span className={`badge status status-${status}`}>{statusLabels[status]}</span>;
}

export function UrgencyBadge({ tier, score }: { tier: UrgencyTier; score: number }) {
  return (
    <span className={`badge urgency urgency-${tier.toLowerCase()}`} aria-label={`${tier} Urgency, score ${score}`}>
      <span aria-hidden="true">{tier === "Critical" ? "◆" : tier === "High" ? "▲" : "●"}</span>
      {tier} · {score}
    </span>
  );
}

export function StateBadge({ value }: { value: string }) {
  return <span className="badge state-badge">{sentenceCase(value)}</span>;
}
