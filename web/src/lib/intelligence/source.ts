import type { IntelligenceRun } from "./types";
import type { WorkbenchModel } from "@/lib/workbench/types";

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
}

/** A separately fetched narrative file must describe exactly the adopted Book. */
export function intelligenceMatchesWorkbench(run: IntelligenceRun | null, model: WorkbenchModel): boolean {
  return Boolean(run?.workbench && canonical(run.workbench) === canonical(model));
}

export function analysisErrorMessage(payload: unknown, status: number): string {
  if (payload && typeof payload === "object") {
    const body = payload as Record<string, unknown>;
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.diagnostics)) {
      const messages = body.diagnostics.flatMap((item: unknown) => {
        if (!item || typeof item !== "object") return [];
        const diagnostic = item as Record<string, unknown>;
        return typeof diagnostic.message === "string" ? [diagnostic.message] : [];
      });
      if (messages.length) return messages.slice(0, 5).join(" ");
    }
  }
  return `Analysis failed (${status}). Check the complete dataset and try again.`;
}
