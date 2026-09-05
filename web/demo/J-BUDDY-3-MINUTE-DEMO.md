# J Buddy — three people, three minutes

## Setup (before the timer)

Use one laptop and one browser. Person 2 operates the mouse throughout; the other speakers face the judges. Open `http://127.0.0.1:3000`, reload to clear rehearsal approvals, and leave the full Priority Queue visible. Use the supplied Book, **as of 26 August 2026**, not today's date. Rehearse at 1440 × 900 or the actual projector resolution.

The spoken text below is approximately 350 words. Aim for conversational delivery, leaving several seconds per minute for clicks. Bracketed directions are not spoken. Do not improvise investment promises or numerical claims.

## Person 1 · 0:00–1:00 · The right conversation, not another dashboard

[0:00: Show the full Priority Queue. Aishah is genuinely first; do not reorder it.]

“Twenty clients. One relationship manager. The challenge isn't another chart: it's knowing who needs a conversation, why now, and how to begin.

J Buddy turns portfolio data and relationship notes into an evidence-backed action list. Aishah ranks first because of an unwaived binding mandate exclusion—not because we selected her for the demo. Urgency and confidence are separate.

[0:25: Click **Cheung**. Point to the income conflict under **Confirm before acting**.]

Cheung shows why context matters. He wants income and capital preservation, but is reluctant to sell bonds at a loss. His stated annual need is 1.1 million US dollars; the recorded obligation is 1.28 million. We show both and ask which is current.

That changes the conversation from ‘sell your bonds’ to ‘let's clarify your income needs and funding options.’”

## Person 2 · 1:00–2:00 · Hidden risk, with proof

[1:00: Click **Hartono**. Point to the current/historical distinction and the portfolio charts.]

“Hartono's borrowing ratio has recovered to 59.15 percent. But his eight-million-Singapore-dollar borrowing hasn't fallen: collateral lending value rose.

Across his portfolios, direct energy holdings and structured-product underlyings reveal overlapping exposure. That's important because his family business is also energy-linked, and he wants diversification and funding for a property purchase.

[1:25: In the client pulse, expand **Evidence · … cited records**; open the historical LTV record.]

Here is the source record and calculation. We distinguish an old breach from today's position instead of manufacturing an emergency.

[1:38: Close the work surface. Click **Explore supplied collateral what-if**; select **-15% collateral · near**.]

Under this illustrative fifteen-percent collateral decline, his ratio reaches 69.59 percent, near the seventy-percent trigger. It's a scenario, not a forecast.

The next step is a lending conversation that respects his family's constraints—not an automatic trade.”

## Person 3 · 2:00–3:00 · Personal, actionable, RM-controlled

[2:00: Close the work surface. Click **Margarethe**. Point to the tax obligation and Conservative profile.]

“Margarethe needs a different conversation: an inherited portfolio, conservative goals, and a 3.4-million-euro inheritance-tax obligation. J Buddy connects the deadline, accessible funding and life transition. Tax opportunities require specialist review, not invented relief claims.

[2:17: Click **Review Client-Ready View**. Show English alongside German.]

The conversation draft is available in her reporting language, alongside the canonical version.

[2:28: Close the work surface. Click **Prepare conversation**, then **Approve**, then **Mark conversation prepared**.]

The RM reviews and approves the brief. Changing it invalidates approval. Nothing is sent or traded.

Our working prototype separates deterministic analytics, cited evidence and optional Gemini wording. The core demo works offline; production security and integration are explicitly a next stage.

For Julius Baer, this means earlier, more personal, defensible conversations across the Book—technology strengthening the relationship manager, not replacing one.”

## Click discipline and fallback

- Rehearse the scroll positions; **Prepared views** is below the advisory cards. Use the browser's find function during rehearsal to locate buttons, not during the pitch.
- At 1:45, skip the evidence expansion if running late, but keep the what-if and its “not a forecast” statement.
- At 2:30, move immediately to the approval sequence. End at three minutes; do not add the upload or architecture tour.
- If the browser fails, use the refreshed screenshots in `screenshots/`: `01`, `02`, `03`, `07`, `08`. Say “This is our captured local run,” not “live.”
- The tax amount and deadline are supplied data, not a tax calculation. The current artifact says 36 days remaining at its analysis date.
- Hartono's energy look-through is indicative: component weights are absent. Do not present it as a precise sensitivity or percentage of his entire external wealth.

## After the timer: short answers to likely judge questions

**Can I upload another Book?** “Yes: the complete supported CSV/JSON dataset or an Excel workbook with the required sheets. Upload and analyse runs validation, analytics and ranking. Incomplete or unmapped data is reported, not guessed.” Offer a live upload after the timed story; allow processing time.

**Is that live Gemini?** “This local run uses deterministic insights and cached language. Gemini refinement is integrated but requires a server-side API key; it is not enabled on this machine. Model wording is constrained and checked, and still needs RM review.” Do not claim a live model call was tested.

**Why not just ChatGPT?** “Our distinguishing workflow is governed calculations, reproducible ranking, traceable records and approval linked to a draft revision—not an unrestricted chat response.”

**Is it production-ready?** “No. We demonstrate the workflow and contract boundary; identity, access controls, durable audit and bank-system integration need production validation.” Open **Target architecture** only if asked.

**How would you measure success?** “A pilot would measure time to prepare an approved brief, missed urgent obligations, and the proportion of suggested conversations the RM accepts. We have not yet measured those outcomes.”
