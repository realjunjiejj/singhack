# JB Clarity RM Intelligence Workbench

Desktop-first Next.js workbench for Priscilla Ong’s Priority Queue → Client Case → Evidence Chain → Meeting Brief workflow. It consumes only the versioned Workbench contract and contains no financial calculations, ranking logic, browser translation, trade execution, messaging, or persistent workflow state.

## Local upload and automatic analysis

From the repository root:

```powershell
& "$env:LOCALAPPDATA\Python\bin\python.exe" -m pip install -e ".\engine[api,dev]"
cd web
npm ci
npm run dev:full
```

Open `http://localhost:3000`, then choose **Upload & analyse**. Upload either all canonical CSV/JSON files or one Excel workbook whose sheets use the canonical table names shown in the dialog. The uploaded Book, Priority Queue, Client Cases, portfolio charts, and specialist insights replace the displayed artifact automatically after validation and analysis.

`npm run dev:full` starts both the Next.js site and local Python analysis API. If Python is installed elsewhere, set `JB_CLARITY_PYTHON` to that executable first.

Gemini is optional. Deterministic analytics and every insight lens work without a key. To enable Gemini wording refinement for deep Hidden Risk and Prioritisation findings, set the key only in the server environment before starting:

```powershell
$env:GEMINI_API_KEY="your-key"
cd web
npm run dev:full
```

Never place the key in browser code or commit it. Generated language is accepted only when it remains inside the selected Evidence Packets; otherwise deterministic wording is retained.

`sync-data` selects `../artifacts/workbench.json` when it exists and validates against schema `1.0.0`; otherwise it uses `../artifacts/workbench.fixture.json`. Incompatible input is rejected rather than repaired.

## Offline demonstration

Install dependencies once while online. Then disconnect networking and run:

```bash
cd web
npm run sync-data
npm run build
npm run start
```

No AI key or network connection is used. The fixture is visibly marked `Demo fixture · partial Book`; a generated artifact is labeled with its data-quality status. Cached Client-Ready drafts remain available if supplied by the artifact.

## Verification

```powershell
cd web
npm test
npm run test:e2e
npm run build
```

From the repository root, verify the analysis engine with:

```powershell
& "$env:LOCALAPPDATA\Python\bin\python.exe" -m pytest engine/tests -q
```

Playwright writes rehearsal screenshots to `demo/screenshots/` for the Queue, Hartono Evidence Chain, approved Meeting Brief, responsive widths, Cheung and Margarethe bilingual views, and target architecture. The repository includes Builder 1’s generated 20-client artifact; the fixture remains only as a fallback.

## Demo path

1. Frame Priscilla’s attention problem; the Queue is already in artifact order.
2. Select Hartono and state that the 78.50% and 75.68% breaches are historical and resolved; current LTV is 59.15%.
3. Open an evidence citation to show exact source record, value, lending-value formula inputs, interpretation, and advisory significance.
4. Open the supplied collateral what-if and choose the 15%-down scenario. It is explicitly not a forecast and is never recalculated in the browser.
5. Prepare the Meeting Brief, edit the opening question, approve the current revision, and mark the conversation prepared.
6. Edit the approved brief to show approval and Case Resolution being invalidated.
7. Use the Demo cases chips for Cheung and Margarethe when the generated artifact is present; compare their cached Traditional Chinese and German drafts.
8. Open Target architecture and distinguish demonstrated capabilities from target bank controls.

## Artifact adoption record

`npm run sync-data` prints the adopted source path, artifact kind, and schema version. A valid `artifacts/workbench.json` replaces fixture mode through the same adapter. If its shape, version, packet ownership, or citation targets are incompatible, the UI blocks adoption and explains how to regenerate and sync it.

## Boundaries and attribution

The implementation is original. Advisor Desktop was inspected for compact-card, expandable-detail, filtering, and presentation/service-boundary patterns; Anthropic Financial Services was inspected for Meeting Brief staging and no-send/human-review guardrails. No third-party source code or text was materially copied, so no third-party notice is required.
