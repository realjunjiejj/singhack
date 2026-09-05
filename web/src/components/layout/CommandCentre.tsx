"use client";

import Link from "next/link";
import { useEffect, useMemo, useReducer, useState } from "react";
import { ClientCasePanel } from "@/components/case/ClientCasePanel";
import { ErrorState } from "@/components/common/ErrorState";
import { EvidenceLabelsProvider } from "@/components/common/EvidenceLabels";
import { PriorityQueue } from "@/components/queue/PriorityQueue";
import { DatasetUpload } from "@/components/upload/DatasetUpload";
import { WorkSurface } from "@/components/work-surface/WorkSurface";
import type { IntelligenceRun } from "@/lib/intelligence/types";
import { isIntelligenceRun } from "@/lib/intelligence/types";
import { intelligenceMatchesWorkbench } from "@/lib/intelligence/source";
import type { EditableBrief } from "@/lib/state/model";
import { createInitialState } from "@/lib/state/model";
import { workbenchReducer } from "@/lib/state/reducer";
import { adoptWorkbench, loadWorkbench, WorkbenchAdapterError } from "@/lib/workbench/adapter";
import { formatDate } from "@/lib/workbench/format";
import { evidenceExists, getCase } from "@/lib/workbench/selectors";
import type { ClientCase, MeetingBriefSeed, OpenLoopStateValue, WorkbenchModel } from "@/lib/workbench/types";

function snapshotDefaults(clientCase: ClientCase): [string, string] {
  const first = clientCase.timeline[0]?.date ?? "";
  const last = clientCase.timeline.at(-1)?.date ?? first;
  return [first, last];
}

function editableSeed(seed: MeetingBriefSeed): EditableBrief {
  return {
    whatChanged: seed.whatChanged,
    whyItMatters: seed.whyItMatters,
    uncertainties: seed.uncertainties,
    openingQuestion: seed.openingQuestion,
    discussionOptions: seed.discussionOptions,
    specialistSuggestion: seed.specialistSuggestion,
  };
}

export function CommandCentre() {
  const [model, setModel] = useState<WorkbenchModel | null>(null);
  const [intelligenceRun, setIntelligenceRun] = useState<IntelligenceRun | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [state, dispatch] = useReducer(workbenchReducer, undefined, createInitialState);

  useEffect(() => {
    let current = true;
    Promise.all([
      loadWorkbench(),
      fetch("/data/intelligence.json", { cache: "no-store" })
        .then(async (response) => response.ok ? response.json() as Promise<unknown> : null)
        .then((payload) => isIntelligenceRun(payload) ? payload : null)
        .catch(() => null),
    ])
      .then(([loaded, run]) => {
        if (!current) return;
        setModel(loaded);
        setIntelligenceRun(intelligenceMatchesWorkbench(run, loaded) ? run : null);
        dispatch({ type: "SOURCE_READY", artifactKind: loaded.meta.artifactKind, schemaVersion: loaded.meta.schemaVersion });
        const first = loaded.book.priorityQueue[0];
        const firstCase = first ? getCase(loaded, first.caseId) : null;
        if (firstCase) {
          dispatch({
            type: "SELECT_CASE",
            caseId: firstCase.caseId,
            snapshots: snapshotDefaults(firstCase),
            stressScenarioId: firstCase.collateralStressTest?.scenarios[0]?.id,
          });
        }
      })
      .catch((error: unknown) => {
        if (!current) return;
        const adapterError = error instanceof WorkbenchAdapterError ? error : new WorkbenchAdapterError(error instanceof Error ? error.message : String(error));
        dispatch({ type: "SOURCE_ERROR", error: adapterError.message, schemaVersion: adapterError.receivedVersion });
      });
    return () => { current = false; };
  }, []);

  const clientCase = useMemo(() => model ? getCase(model, state.activeCaseId) : null, [model, state.activeCaseId]);
  const casePackets = useMemo(() => model && clientCase ? model.evidencePackets.filter((packet) => packet.caseId === clientCase.caseId) : [], [model, clientCase]);
  if (state.source.status === "error") return <ErrorState message={state.source.error ?? "Unknown artifact error"} receivedVersion={state.source.schemaVersion} />;
  if (!model || state.source.status === "loading") return <LoadingState />;

  const selectCase = (caseId: string) => {
    const selected = getCase(model, caseId);
    if (!selected) return;
    dispatch({ type: "SELECT_CASE", caseId, snapshots: snapshotDefaults(selected), stressScenarioId: selected.collateralStressTest?.scenarios[0]?.id });
  };
  const adoptAnalysis = async (run: IntelligenceRun) => {
    if (!run.workbench) throw new WorkbenchAdapterError("The analysis completed without a presentable Workbench artifact.");
    const loaded = await adoptWorkbench(run.workbench);
    const first = loaded.book.priorityQueue[0];
    const firstCase = first ? getCase(loaded, first.caseId) : null;
    setModel(loaded);
    setIntelligenceRun(run);
    dispatch({ type: "SOURCE_READY", artifactKind: loaded.meta.artifactKind, schemaVersion: loaded.meta.schemaVersion });
    if (firstCase) dispatch({ type: "SELECT_CASE", caseId: firstCase.caseId, snapshots: snapshotDefaults(firstCase), stressScenarioId: firstCase.collateralStressTest?.scenarios[0]?.id });
    setUploadOpen(false);
  };
  const openEvidence = (evidenceId: string) => {
    if (!clientCase || !evidenceExists(model, clientCase.caseId, evidenceId)) return;
    dispatch({ type: "OPEN_SURFACE", caseId: clientCase.caseId, surface: "evidence", evidenceItemId: evidenceId });
  };
  const openQueueEvidence = (caseId: string, evidenceId: string) => {
    const selected = getCase(model, caseId);
    if (!selected || !evidenceExists(model, caseId, evidenceId)) return;
    if (state.activeCaseId !== caseId) {
      dispatch({ type: "SELECT_CASE", caseId, snapshots: snapshotDefaults(selected), stressScenarioId: selected.collateralStressTest?.scenarios[0]?.id });
    }
    dispatch({ type: "OPEN_SURFACE", caseId, surface: "evidence", evidenceItemId: evidenceId });
  };
  const prepareBrief = () => {
    if (!clientCase) return;
    dispatch({ type: "PREPARE_BRIEF", caseId: clientCase.caseId, seed: editableSeed(clientCase.meetingBrief) });
  };
  const handleGuidedAction = (action: string) => {
    if (!clientCase) return;
    if (action === "show-evidence" || action === "explain") {
      const firstEvidence = clientCase.facts[0]?.evidenceItemIds[0] ?? clientCase.evidencePacketIds[0];
      if (firstEvidence) openEvidence(firstEvidence);
    } else if (action === "prepare-conversation") {
      prepareBrief();
    } else if (action === "stress-test") {
      dispatch({ type: "OPEN_SURFACE", caseId: clientCase.caseId, surface: "stress-test" });
    } else if (action === "client-ready") {
      dispatch({ type: "OPEN_SURFACE", caseId: clientCase.caseId, surface: "client-ready" });
    } else if (action === "request-information") {
      dispatch({ type: "SET_CASE_RESOLUTION", caseId: clientCase.caseId, resolution: "information-requested" });
      prepareBrief();
    } else if (action === "involve-specialist") {
      dispatch({ type: "SET_CASE_RESOLUTION", caseId: clientCase.caseId, resolution: "specialist-involved" });
      prepareBrief();
    } else if (action === "confirm-open-loop" && clientCase.openLoops[0]) {
      dispatch({ type: "SET_OPEN_LOOP_STATE", openLoopId: clientCase.openLoops[0].id, state: "confirmed" });
    } else if (["defer-open-loop", "assign-open-loop", "dismiss-open-loop"].includes(action)) {
      const relationshipDetail = document.querySelector<HTMLDetailsElement>(".support-details:not(.comparison-details)");
      if (relationshipDetail) relationshipDetail.open = true;
      window.setTimeout(() => document.querySelector<HTMLElement>(".open-loop input")?.focus(), 0);
    } else if (action === "dismiss-case") {
      prepareBrief();
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <img src="/julius-baer-logo.png" alt="Julius Bär" className="brand-logo" />
          <div className="brand-divider" aria-hidden="true" />
          <div><strong>J Buddy</strong><small>RM Intelligence Workbench</small></div>
        </div>
        <p className="promise">Know who to call, why, and how to begin.</p>
        <div className="topbar-meta">
          <span><small>As of</small>{formatDate(model.meta.asOfDate)}</span>
          <span><small>Relationship Manager</small>{model.book.rm.name}</span>
          <span className={`artifact-pill ${model.meta.artifactKind}`}><i />{model.meta.artifactKind === "fixture" ? "Demo fixture · partial Book" : `Generated · ${model.meta.dataQuality.status}`}</span>
          <button type="button" className="upload-trigger" onClick={() => setUploadOpen(true)}>Upload &amp; analyse</button>
          <Link href="/architecture">Target architecture ↗</Link>
        </div>
      </header>
      <div className="command-centre">
        <EvidenceLabelsProvider model={model}>
          <PriorityQueue model={model} state={state} onFilters={(filters) => dispatch({ type: "SET_FILTERS", filters })} onSelect={selectCase} onEvidence={openQueueEvidence} />
          <ClientCasePanel
            model={model}
            clientCase={clientCase}
            evidencePackets={casePackets}
            agentReports={intelligenceRun?.agentReports ?? []}
            state={state}
            onEvidence={openEvidence}
            onOpenLoop={(id: string, value: OpenLoopStateValue, note?: string) => dispatch({ type: "SET_OPEN_LOOP_STATE", openLoopId: id, state: value, note })}
            onSnapshots={(snapshots) => dispatch({ type: "SELECT_SNAPSHOTS", snapshots })}
            onGuidedAction={handleGuidedAction}
          />
          <WorkSurface
            model={model}
            clientCase={clientCase}
            state={state}
            onClose={() => dispatch({ type: "CLOSE_SURFACE" })}
            onEvidence={openEvidence}
            onBack={() => document.getElementById("active-client-case")?.focus()}
            onScenario={(scenarioId) => dispatch({ type: "SELECT_STRESS_SCENARIO", scenarioId })}
            onEditBrief={(field, value) => clientCase && dispatch({ type: "EDIT_BRIEF_FIELD", caseId: clientCase.caseId, field, value })}
            onResetBrief={() => clientCase && dispatch({ type: "RESET_BRIEF", caseId: clientCase.caseId })}
            onApproveBrief={() => clientCase && dispatch({ type: "APPROVE_BRIEF", caseId: clientCase.caseId })}
            onResolve={(resolution, reason) => clientCase && dispatch({ type: "SET_CASE_RESOLUTION", caseId: clientCase.caseId, resolution, reason })}
            onGuidedAction={handleGuidedAction}
          />
        </EvidenceLabelsProvider>
      </div>
      {uploadOpen && <DatasetUpload onClose={() => setUploadOpen(false)} onComplete={adoptAnalysis} />}
    </div>
  );
}

function LoadingState() {
  return (
    <main className="loading-state" aria-live="polite">
      <span className="loading-mark" aria-hidden="true" />
      <p className="eyebrow">J Buddy</p><h1>Validating the Workbench artifact…</h1>
      <p>No Client Case is available until the versioned boundary is compatible.</p>
    </main>
  );
}
