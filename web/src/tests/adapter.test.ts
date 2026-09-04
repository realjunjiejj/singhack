import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { validateWorkbenchModel } from "@/lib/workbench/schema";

const schema = JSON.parse(readFileSync(path.resolve(process.cwd(), "../contracts/workbench.schema.json"), "utf8"));
const fixture = JSON.parse(readFileSync(path.resolve(process.cwd(), "../artifacts/workbench.fixture.json"), "utf8"));

describe("Workbench contract boundary", () => {
  it("accepts the repository fixture", () => {
    const result = validateWorkbenchModel(fixture, schema);
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.data.clientCases[0]?.clientId).toBe("CL-0001");
  });

  it("rejects malformed input with an actionable message", () => {
    const result = validateWorkbenchModel({ meta: { schemaVersion: "1.0.0" } }, schema);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toMatch(/validation failed.*sync-data/i);
  });

  it("rejects a schema mismatch rather than coercing it", () => {
    const wrongVersion = structuredClone(fixture);
    wrongVersion.meta.schemaVersion = "2.0.0";
    const result = validateWorkbenchModel(wrongVersion, schema);
    expect(result).toMatchObject({ ok: false, receivedVersion: "2.0.0" });
    if (!result.ok) expect(result.message).toContain("Expected 1.0.0; received 2.0.0");
  });

  it("rejects a claim whose evidence target is missing", () => {
    const broken = structuredClone(fixture);
    broken.clientCases[0].facts[0].evidenceItemIds = ["E-DOES-NOT-EXIST"];
    const result = validateWorkbenchModel(broken, schema);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("cites missing evidence E-DOES-NOT-EXIST");
  });
});
