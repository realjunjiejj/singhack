# J Buddy — judging alignment and rehearsal checklist

Reviewed against `singhacks-jb-wealth-intelligence/README.md`, the local specification and ADRs. The organizer rewards defensible reasoning, judgment, explicit uncertainty and human control; depth on two or three clients beats breadth without substance. No implementation can guarantee the judging outcome.

## Equal-weight judging criteria

| Criterion (25% each) | Concrete demonstration | Avoid claiming |
| --- | --- | --- |
| Client-centric innovation | Cheung's conflicting income needs; Hartono's business/portfolio overlap; Margarethe's inheritance and tax deadline | A generic “AI recommends selling” story |
| User experience and design | Honest Priority Queue → client context/charts → source evidence → reviewed brief; bilingual drafts | That more screens or text are themselves innovation |
| Technical and operational feasibility | Versioned validated artifacts, deterministic ranking, source formulas, offline core, revision-specific approval | Production bank security, persistent audit, or hallucination-proof AI |
| Strategic impact | A practical RM conversation workflow across the Book, with personal context preserved | Measured time savings, returns or client outcomes without a pilot |

Five requested advisory lenses remain available: personalised discussion options, rebalancing considerations, tax-aware review, life-event needs, and whole-Book priority. Tax awareness is not jurisdiction-specific tax advice or household optimisation: required household and tax-rule inputs are absent.

## Changes in this pass

- Preserved the existing interface layout and prior J Buddy rename.
- Replaced the executive panel's hand-authored client-ID stories with the adopted case's facts, uncertainties, discussion options and opening question. The old stories included inconsistent trigger values, dates, amounts and unsupported guarantees.
- Prevented separately cached specialist narratives from attaching to a different Workbench, even when client IDs match.
- Regenerated the Workbench and intelligence files as a matching pair at a fixed generation timestamp.
- Reset draft briefs, approvals, resolutions, notes and filters only after successful adoption of a replacement Book. Invalid uploads retain the existing Book.
- Exposed engine diagnostics on unsuccessful uploads and explained dataset replacement and optional model-provider disclosure.
- Demo shortcuts now feature exactly two cases: #1 Aishah and Cheung. Aishah's label uses her actual artifact rank; underlying queue order is unchanged.
- Added unit regressions and a browser regression for a same-ID dataset replacement after approval.

## Local rehearsal

From `web/`, run `npm.cmd run dev:full`, then open `http://127.0.0.1:3000`. Do not start a second copy if one is already listening. Keep the terminal running. The local engine listens on port 8000.

Before presenting:

1. Confirm the header says **J Buddy**, **26 Aug 2026**, **Priscilla Ong**, and **20/20**.
2. Confirm #1 Aishah and Cheung shortcuts work. Explain Aishah's Critical safety override using her Priority Rationale. Other clients remain accessible in the full queue.
3. Check allocation charts, one source record, the collateral what-if, both translated drafts and the approval workflow.
4. Rehearse the [three-minute script](J-BUDDY-3-MINUTE-DEMO.md) twice with the actual display and a timer.
5. Prepare the screenshot fallback. Avoid running a production build while using the dev server for the presentation.
6. Test uploads before the pitch, not inside its three-minute critical path. Use synthetic challenge data only. Files require the documented canonical structure; arbitrary spreadsheets are not automatically understood.
7. Confirm `/api/analysis/health`. On this audit it reported `ready`, with `geminiConfigured: false`. Deterministic analysis works without a key; live Gemini has not been verified.

The upload browser regression intercepts the response to test UI adoption; it does not by itself prove the live engine. Engine tests and the real CLI analysis run provide separate backend evidence.

## Verification — 5 September 2026

- Web unit tests: **38 passed** (including new source/approval regressions).
- Browser tests: **11 passed** (deep cases, responsive widths, evidence, approval, languages, second Book, upload adoption and offline core).
- Engine tests: **266 passed**; one upstream Starlette/httpx deprecation warning.
- Production build: **passed**.
- Real CLI analysis: **completed**, six specialist reports, schema-validated embedded Workbench; paired artifacts confirmed identical.
- Refreshed demo screenshots; inspected the 1280-pixel overview. `git diff --check` found no whitespace errors.
- No live Gemini request was tested. No production security or performance certification is implied.

## Source-owner follow-up

This pass stays in Builder 2's presentation/workflow slice; engine code and financial rules have not been changed. These engine-source copy issues were found and should be reviewed by Builder 1 before treating all generated wording as client-ready:

- `engine/src/jb_clarity/build.py`: the Hartono opening question still says “credit headroom remains completely secure”. That is too absolute. During review, change it to “review funding options and the remaining credit headroom”. The lending-specialist sentence also repeats its confirmation clause.
- `engine/src/jb_clarity/detectors/evidence_conflicts.py`: the objective-gap formula divides by the planned amount, but the sentence describes the result as “higher”. Use “a gap equal to … of the recorded obligation”, or explicitly change the denominator and its tests. The timed script quotes the two amounts without this misleading percentage.
- Engine opening questions contain demo-ID-specific phrasing. The frontend no longer adds such stories, but fully generic source generation requires the engine owner to derive those openings from the new Book's actual context. Do not describe arbitrary same-ID uploads as semantically safe end to end on the strength of frontend tests alone.

Other deliberate limits: model output checks are not proof of semantic truth; cached translations need RM review; workflow state is local and not durable; no messages or trades are executed; collateral scenarios are illustrative; event linkage is not measured performance attribution; production identity, authorisation, audit, retention and bank integration remain a separate deployment gate. Upload processing is by the configured service, and optional Gemini can send selected summaries to its provider.
