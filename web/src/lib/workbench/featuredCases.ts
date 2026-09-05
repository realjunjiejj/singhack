import type { PriorityQueueItem } from "./types";

/**
 * The three SingHacks demonstration clients, in the order the pitch walks them.
 * Their presence is what makes an artifact "the demonstration Book"; nothing
 * else in the interface may depend on these identifiers.
 */
const SINGHACKS_DEMO_CASES = [
  { clientId: "CL-0005", label: "#1 Aishah" },
  { clientId: "CL-0012", label: "Cheung" },
] as const;

export const MAX_FEATURED_CASES = 3;

export type FeaturedCase = {
  caseId: string;
  clientId: string;
  label: string;
};

export type FeaturedCases = {
  /** "Demo cases" for the SingHacks Book, "Featured cases" for any other. */
  heading: string;
  isDemoBook: boolean;
  cases: FeaturedCase[];
};

/** A short, recognisable label for a client the artifact actually contains. */
function shortLabel(clientName: string): string {
  const trimmed = clientName.trim();
  if (!trimmed) return "Client";
  // Prefer a surname, which is how an RM refers to a client in conversation,
  // but fall back to the whole name rather than inventing one.
  const parts = trimmed.split(/\s+/);
  const surname = parts.length > 1 ? parts[parts.length - 1] : parts[0];
  return surname.replace(/[^\p{L}\p{N}\-']/gu, "") || trimmed;
}

/**
 * Quick-access shortcuts for the queue.
 *
 * The hackathon shortcuts are kept exactly when the demonstration clients are
 * present. Any other Book gets shortcuts derived from its own Priority Queue
 * order, so a shortcut always points at a case the artifact contains. A
 * shortcut is never rendered for an identifier that is absent.
 */
export function selectFeaturedCases(queue: readonly PriorityQueueItem[]): FeaturedCases {
  const byClient = new Map(queue.map((item) => [item.clientId, item]));

  const demo = SINGHACKS_DEMO_CASES.flatMap(({ clientId, label }) => {
    const item = byClient.get(clientId);
    return item ? [{ caseId: item.caseId, clientId, label }] : [];
  });

  if (demo.length === SINGHACKS_DEMO_CASES.length) {
    return { heading: "Demo cases", isDemoBook: true, cases: demo };
  }

  return {
    heading: "Featured cases",
    isDemoBook: false,
    // Queue order is the artifact's own priority order; the shortcuts must not
    // imply a different ranking from the list directly beneath them.
    cases: queue.slice(0, MAX_FEATURED_CASES).map((item) => ({
      caseId: item.caseId,
      clientId: item.clientId,
      label: shortLabel(item.clientName),
    })),
  };
}
