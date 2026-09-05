import type { ClientCase } from "@/lib/workbench/types";

/** Presentation only: never substitute a story selected by client ID. */
export function getExecutiveInsight(clientCase: ClientCase) {
  const brief = clientCase.meetingBrief;
  return {
    headline: clientCase.conclusion,
    whatHappened: {
      summary: brief.whatChanged,
      metrics: [
        { label: "Urgency", value: clientCase.urgency.tier },
        { label: "Confidence (not probability)", value: clientCase.confidence.level },
        { label: "Case status", value: clientCase.status.replace(/-/g, " ") },
      ],
    },
    clientDilemma: {
      tension: brief.whyItMatters,
      trapSummary: brief.uncertainties.join(" ") || "No additional uncertainty supplied. Confirm suitability and current circumstances with the client before acting.",
    },
    whatShouldBeDone: brief.discussionOptions.map((detail, index) => ({
      title: `Discussion option ${index + 1}`,
      detail,
    })),
    conversationScript: {
      opener: brief.openingQuestion,
      whyItWorks: brief.specialistSuggestion || "Review this draft with the client's objectives and constraints before use. Nothing is sent or traded.",
    },
  };
}
