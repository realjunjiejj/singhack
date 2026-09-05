import { access, copyFile, mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.resolve(HERE, "..");
const REPO_ROOT = path.resolve(WEB_ROOT, "..");
const REPO_SCHEMA_PATH = path.join(REPO_ROOT, "contracts", "workbench.schema.json");
const GENERATED_PATH = path.join(REPO_ROOT, "artifacts", "workbench.json");
const FIXTURE_PATH = path.join(REPO_ROOT, "artifacts", "workbench.fixture.json");
const OUTPUT_DIR = path.join(WEB_ROOT, "public", "data");
const OUTPUT_PATH = path.join(OUTPUT_DIR, "workbench.json");
const OUTPUT_SCHEMA_PATH = path.join(OUTPUT_DIR, "workbench.schema.json");
const EXPECTED_VERSION = "1.0.0";

async function exists(file) {
  try {
    await access(file);
    return true;
  } catch {
    return false;
  }
}

const SCHEMA_PATH = await exists(REPO_SCHEMA_PATH) ? REPO_SCHEMA_PATH : OUTPUT_SCHEMA_PATH;
const schema = JSON.parse(await readFile(SCHEMA_PATH, "utf8"));
const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
const validate = ajv.compile(schema);

async function inspect(file) {
  try {
    const parsed = JSON.parse(await readFile(file, "utf8"));
    const version = parsed?.meta?.schemaVersion;
    if (version !== EXPECTED_VERSION) {
      return { ok: false, reason: `schema mismatch (expected ${EXPECTED_VERSION}, received ${version ?? "unknown"})` };
    }
    if (!validate(parsed)) return { ok: false, reason: ajv.errorsText(validate.errors, { separator: "; " }) };
    return { ok: true, data: parsed };
  } catch (error) {
    return { ok: false, reason: error instanceof Error ? error.message : String(error) };
  }
}

const generatedExists = await exists(GENERATED_PATH);
const candidates = [
  ...(generatedExists ? [GENERATED_PATH] : []),
  ...((await exists(OUTPUT_PATH)) ? [OUTPUT_PATH] : []),
  ...((await exists(FIXTURE_PATH)) ? [FIXTURE_PATH] : []),
];
let selected;
for (const candidate of candidates) {
  const result = await inspect(candidate);
  if (result.ok) {
    selected = { path: candidate, data: result.data, retained: candidate === OUTPUT_PATH };
    break;
  }
  console.warn(`[sync-data] rejected ${path.relative(REPO_ROOT, candidate)}: ${result.reason}`);
}

if (!selected) {
  throw new Error("No compatible Workbench artifact is available. Regenerate artifacts/workbench.json or repair the fixture.");
}

await mkdir(OUTPUT_DIR, { recursive: true });
if (!selected.retained) await copyFile(selected.path, OUTPUT_PATH);
if (SCHEMA_PATH !== OUTPUT_SCHEMA_PATH) await copyFile(SCHEMA_PATH, OUTPUT_SCHEMA_PATH);
console.log(
  `[sync-data] source=${path.relative(REPO_ROOT, selected.path)}${selected.retained ? " (retained last compatible artifact)" : ""} schema=${selected.data.meta.schemaVersion} kind=${selected.data.meta.artifactKind}`,
);
