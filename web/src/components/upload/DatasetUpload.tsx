"use client";

import { useEffect, useRef, useState, type DragEvent, type FormEvent } from "react";
import type { IntelligenceRun } from "@/lib/intelligence/types";
import { isIntelligenceRun } from "@/lib/intelligence/types";
import { analysisErrorMessage } from "@/lib/intelligence/source";

type EngineHealth = { status: string; geminiConfigured: boolean; detail?: string };

export function DatasetUpload({ onClose, onComplete }: {
  onClose: () => void;
  onComplete: (run: IntelligenceRun) => Promise<void>;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [health, setHealth] = useState<EngineHealth>({ status: "checking", geminiConfigured: false });
  const [liveAi, setLiveAi] = useState(false);
  const [asOfDate, setAsOfDate] = useState("");
  const [status, setStatus] = useState<"idle" | "running" | "done">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/analysis/health", { cache: "no-store" })
      .then(async (response) => ({ response, body: await response.json() as EngineHealth }))
      .then(({ response, body }) => {
        setHealth(response.ok ? body : { ...body, status: "unavailable" });
        setLiveAi(response.ok && body.geminiConfigured);
      })
      .catch(() => setHealth({ status: "unavailable", geminiConfigured: false, detail: "The local analysis engine is not running." }));
  }, []);

  const chooseFiles = (selected: FileList | null) => {
    if (!selected) return;
    setFiles(Array.from(selected));
    setError("");
    setStatus("idle");
  };

  const drop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    chooseFiles(event.dataTransfer.files);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (files.length === 0) {
      setError("Select the canonical customer-data files or one workbook containing the canonical sheets.");
      return;
    }
    setStatus("running");
    setError("");
    const body = new FormData();
    files.forEach((file) => body.append("files", file, file.name));
    body.append("live_ai", String(liveAi));
    if (asOfDate) body.append("as_of_date", asOfDate);

    try {
      const response = await fetch("/api/analysis", { method: "POST", body });
      const payload: unknown = await response.json();
      if (!response.ok) {
        throw new Error(analysisErrorMessage(payload, response.status));
      }
      if (!isIntelligenceRun(payload) || !payload.workbench) throw new Error("The engine returned no compatible Workbench artifact.");
      await onComplete(payload);
      setStatus("done");
    } catch (failure) {
      setStatus("idle");
      setError(failure instanceof Error ? failure.message : String(failure));
    }
  };

  return (
    <div className="upload-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && status !== "running") onClose(); }}>
      <section className="upload-dialog" role="dialog" aria-modal="true" aria-labelledby="upload-title">
        <header className="upload-header">
          <div><p className="eyebrow">New intelligence run</p><h1 id="upload-title">Analyse a customer Book</h1></div>
          <button type="button" className="icon-button" onClick={onClose} disabled={status === "running"} aria-label="Close upload">×</button>
        </header>
        <p className="upload-intro">Upload the complete customer dataset. Validation, financial analytics, specialist analysis, evidence checks and Priority ranking run automatically.</p>

        <form onSubmit={submit}>
          <div className="upload-dropzone" onDragOver={(event) => event.preventDefault()} onDrop={drop}>
            <span className="upload-icon" aria-hidden="true">⇧</span>
            <strong>Drop CSV/JSON files or an Excel workbook</strong>
            <p>Use the canonical filenames, or workbook sheets named clients, portfolios, holdings, instruments, mandates, transactions, credit_facilities, commitments, planned_cash_needs, market_context, event_log and rm_notes.</p>
            <button type="button" onClick={() => inputRef.current?.click()}>Choose files</button>
            <input ref={inputRef} className="sr-only" type="file" multiple accept=".csv,.json,.xlsx,.xls" aria-label="Choose files" onChange={(event) => chooseFiles(event.target.files)} />
          </div>

          {files.length > 0 && (
            <div className="selected-files">
              <div><strong>{files.length} file{files.length === 1 ? "" : "s"} selected</strong><button type="button" className="text-button" onClick={() => setFiles([])}>Clear</button></div>
              <ul>{files.slice(0, 6).map((file) => <li key={`${file.name}-${file.size}`}><span>{file.name}</span><small>{(file.size / 1024).toFixed(1)} KB</small></li>)}{files.length > 6 && <li><span>+ {files.length - 6} more files</span></li>}</ul>
            </div>
          )}

          <div className="upload-options">
            <label><span>Analysis date <small>(optional)</small></span><input type="date" value={asOfDate} onChange={(event) => setAsOfDate(event.target.value)} /></label>
            <label className={`ai-toggle ${!health.geminiConfigured ? "is-disabled" : ""}`}>
              <input type="checkbox" checked={liveAi} disabled={!health.geminiConfigured} onChange={(event) => setLiveAi(event.target.checked)} />
              <span><strong>Gemini narrative refinement</strong><small>{health.geminiConfigured ? "Configured · generated wording must pass the evidence gate" : "API key not configured · deterministic insights remain available"}</small></span>
            </label>
          </div>

          <div className={`engine-status status-${health.status}`}><i aria-hidden="true" /><span><strong>Local analysis engine</strong>{health.status === "ready" ? "Ready" : health.detail ?? "Checking availability…"}</span></div>
          {error && <div className="upload-error" role="alert"><strong>Analysis could not start</strong><span>{error}</span></div>}
          {status === "running" && (
            <div className="analysis-progress" aria-live="polite"><span className="loading-mark" aria-hidden="true" /><div><strong>Analysing the uploaded Book…</strong><small>Validating sources → deterministic analytics → Hidden Risk → Prioritisation → evidence audit{liveAi ? " → Gemini validation" : ""}</small></div></div>
          )}
          <div className="upload-actions">
            <button type="button" onClick={onClose} disabled={status === "running"}>Cancel</button>
            <button type="submit" className="primary-button" disabled={status === "running" || health.status !== "ready"}>{status === "running" ? "Analysis running…" : "Upload & analyse automatically"}</button>
          </div>
          <p className="upload-privacy">A successful upload replaces this session's Book and clears its draft briefs, approvals and case decisions. Files are removed from the service's temporary workspace after the run. Gemini refinement sends selected evidence summaries to the configured model provider when enabled; use only authorised data.</p>
        </form>
      </section>
    </div>
  );
}
