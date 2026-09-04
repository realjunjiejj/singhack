import { validateWorkbenchModel } from "./schema";
import type { WorkbenchModel } from "./types";

export class WorkbenchAdapterError extends Error {
  constructor(
    message: string,
    public readonly receivedVersion?: string,
  ) {
    super(message);
    this.name = "WorkbenchAdapterError";
  }
}

export async function loadWorkbench(fetcher: typeof fetch = fetch): Promise<WorkbenchModel> {
  const [artifactResponse, schemaResponse] = await Promise.all([
    fetcher("/data/workbench.json", { cache: "no-store" }),
    fetcher("/data/workbench.schema.json", { cache: "no-store" }),
  ]);
  if (!artifactResponse.ok) {
    throw new WorkbenchAdapterError(
      `Could not load the Workbench artifact (${artifactResponse.status}). Run npm run sync-data and reload.`,
    );
  }
  if (!schemaResponse.ok) {
    throw new WorkbenchAdapterError(
      `Could not load the Workbench schema (${schemaResponse.status}). Run npm run sync-data and reload.`,
    );
  }
  const [artifact, schema] = await Promise.all([artifactResponse.json(), schemaResponse.json()]);
  const result = validateWorkbenchModel(artifact, schema as object);
  if (!result.ok) throw new WorkbenchAdapterError(result.message, result.receivedVersion);
  return result.data;
}
