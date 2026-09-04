import Ajv2020, { type ErrorObject } from "ajv/dist/2020";
import addFormats from "ajv-formats";
import { SUPPORTED_SCHEMA_VERSION, type WorkbenchModel } from "./types";

export type ValidationResult =
  | { ok: true; data: WorkbenchModel }
  | { ok: false; message: string; receivedVersion?: string; errors?: ErrorObject[] | null };

export function validateWorkbenchModel(input: unknown, schema: object): ValidationResult {
  const receivedVersion =
    typeof input === "object" && input !== null && "meta" in input
      ? String((input as { meta?: { schemaVersion?: unknown } }).meta?.schemaVersion ?? "unknown")
      : undefined;

  if (receivedVersion && receivedVersion !== SUPPORTED_SCHEMA_VERSION) {
    return {
      ok: false,
      receivedVersion,
      message: `Workbench schema mismatch. Expected ${SUPPORTED_SCHEMA_VERSION}; received ${receivedVersion}. Run npm run sync-data after regenerating a compatible artifact.`,
    };
  }

  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(input)) {
    const detail = ajv.errorsText(validate.errors, { separator: "; " });
    return {
      ok: false,
      receivedVersion,
      errors: validate.errors,
      message: `Workbench artifact validation failed. Expected schema ${SUPPORTED_SCHEMA_VERSION}. ${detail}. Regenerate the engine artifact, then run npm run sync-data.`,
    };
  }
  const data = input as WorkbenchModel;
  const semanticError = validateReferences(data);
  if (semanticError) {
    return {
      ok: false,
      receivedVersion,
      message: `Workbench artifact validation failed. Expected schema ${SUPPORTED_SCHEMA_VERSION}. ${semanticError} Regenerate the engine artifact, then run npm run sync-data.`,
    };
  }
  return { ok: true, data };
}

function validateReferences(data: WorkbenchModel): string | null {
  const cases = new Map(data.clientCases.map((clientCase) => [clientCase.caseId, clientCase]));
  for (const row of data.book.priorityQueue) {
    if (!cases.has(row.caseId)) return `Priority Queue case ${row.caseId} has no Client Case.`;
  }
  const packets = new Map(data.evidencePackets.map((packet) => [packet.packetId, packet]));
  for (const clientCase of data.clientCases) {
    const casePackets = clientCase.evidencePacketIds.map((id) => packets.get(id));
    if (casePackets.some((packet) => !packet || packet.caseId !== clientCase.caseId)) {
      return `Client Case ${clientCase.caseId} references a missing or foreign Evidence Packet.`;
    }
    const evidenceIds = new Set(
      casePackets.flatMap((packet) => packet ? [...packet.items.map((item) => item.id), ...packet.derivedMetrics.map((metric) => metric.id)] : []),
    );
    const references = [
      ...clientCase.facts,
      ...clientCase.interpretations,
      ...clientCase.uncertainties,
      ...clientCase.factorContributions,
      ...clientCase.anticipatorySignals,
      ...clientCase.openLoops,
      ...clientCase.governanceClocks,
      ...clientCase.timeline,
      clientCase.meetingBrief,
      ...(clientCase.clientReadyDrafts ?? []),
    ].flatMap((item) => item.evidenceItemIds);
    const missing = references.find((id) => !evidenceIds.has(id));
    if (missing) return `Client Case ${clientCase.caseId} cites missing evidence ${missing}.`;
  }
  return null;
}
