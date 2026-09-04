import { SUPPORTED_SCHEMA_VERSION } from "@/lib/workbench/types";

export function ErrorState({ message, receivedVersion }: { message: string; receivedVersion?: string }) {
  return (
    <main className="fatal-state" role="alert">
      <p className="eyebrow">Artifact adoption blocked</p>
      <h1>JB Clarity could not open this Workbench model.</h1>
      <p>{message}</p>
      <dl>
        <div><dt>Expected schema</dt><dd>{SUPPORTED_SCHEMA_VERSION}</dd></div>
        <div><dt>Received schema</dt><dd>{receivedVersion ?? "Could not determine"}</dd></div>
      </dl>
      <p className="callout">Regenerate a compatible artifact, run <code>npm run sync-data</code>, and reload. No incompatible data was adopted.</p>
    </main>
  );
}
