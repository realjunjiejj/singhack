# Builder 1 handoff — Intelligence Engine

**Branch:** `builder-1/intelligence-engine`
**Verification date:** 2026-09-04
**Artifact published:** `artifacts/workbench.json`
**Artifact kind:** `generated`
**Schema version:** `1.0.0` (unchanged — no contract changes were needed)
**Data-quality status:** `attention`

## For Builder 2

Nothing in your workbench needs to change. The generated artifact uses the same
schema version and the same shapes as `artifacts/workbench.fixture.json`, so
`npm run sync-data` should adopt it through your existing adapter and render 20
Queue rows instead of one.

Regenerate it with:

```bash
python -m pip install -e "engine[dev]"
python -m jb_clarity.cli build --data singhacks-jb-wealth-intelligence/data --as-of 2026-08-26 --output artifacts/workbench.json
```

**No optional fields were added.** Every field the artifact contains is one the
v1.0.0 schema already declares. A sample case is `CASE-CL-0001` and a sample
packet is `PACKET-CL-0001-CREDIT`.

Two things that changed relative to the fixture, both within the contract:

- Evidence item identifiers now carry the signal's discriminator where a client
  has several signals in one family, e.g. `EV-CL-0001-CREDIT-CF_0005-TRIGGER`
  and `EV-CL-0006-CASH_NEED-CN_007_NEED`. They are stable across runs.
- Stress scenario ids are facility-derived: `CF-0005-STRESS-BASE` and
  `CF-0005-STRESS-DOWN-15` rather than the fixture's `H-STRESS-*`. Five clients
  have a facility, so five cases carry a stress test.

## What the artifact contains

| | |
| --- | --- |
| Clients ranked | 20 (contiguous ranks 1–20) |
| Portfolios | 24 |
| Evidence Packets | 116 |
| Evidence items | 271 |
| Derived metrics | 85 (each with formula, inputs, unit, result, snapshot date) |
| Anticipatory Signals | 122 across 10 signal types |
| Open Loop candidates | 18, all `state: candidate`, all `confirmationRequired: true` |
| Governance Clocks | 20 (one KYC clock per client, none overdue) |
| Collateral Stress Tests | 5 |
| Bilingual cases | CL-0003 (German), CL-0012 (Traditional Chinese) |
| Tiers | 1 Critical, 6 High, 13 Watch |

## Verification evidence

| Command | Result |
| --- | --- |
| `python -m pip install -e "engine[dev]"` | Pass |
| `python -m jb_clarity.cli build --data … --output artifacts/workbench.json` | Pass — schema-valid, 20 ranked cases |
| `python -m pytest engine/tests` | Pass — 144 tests |

The build validates against `contracts/workbench.schema.json` before writing.
Repeat runs with the same inputs are semantically identical; with
`--generated-at` fixed they are byte-identical. No network access and no model
credentials are used.

## Priority Queue as generated

Ranking is produced entirely by the configured rules in
`config/scoring.v1.json`. The three demonstration clients were not promoted —
a test asserts they do not occupy the top three slots.

| # | Client | Tier | Score | Confidence | Status |
| --: | --- | --- | --: | --- | --- |
| 1 | CL-0005 Aishah binti Rahman | Critical | 78.0 | High | active |
| 2 | CL-0003 Margarethe Voss-Brenner | High | 95.0 | High | active |
| 3 | CL-0014 Lau Chi Ming | High | 89.0 | High | near |
| 4 | CL-0002 Ravi Chandrasekaran | High | 82.5 | Medium | near |
| 5 | CL-0011 Tan Boon Huat | High | 78.5 | Medium | active |
| 6 | CL-0017 Fong Enterprises Family Office | High | 73.15 | High | near |
| 7 | CL-0001 Hartono Wijaya Kusuma | High | 68.5 | High | historical-resolved |
| 8 | CL-0016 Yamamoto Kenji | Watch | 57.09 | High | active |
| 9 | CL-0009 Andreas Lindqvist | Watch | 47.79 | High | active |
| 10 | CL-0006 Nguyen Thi Bao Tran | Watch | 47.0 | Medium | near |
| 11 | CL-0012 Cheung Kwok Wing | Watch | 44.0 | Medium | active |
| 12 | CL-0004 Chalermchai Suphanburi | Watch | 42.69 | High | active |
| 13–20 | CL-0019, CL-0018, CL-0008, CL-0007, CL-0013, CL-0015, CL-0020, CL-0010 | Watch | 39.5 → 3.0 | | |

The single Critical is a Safety Override, not a high score: CL-0005 holds two
instruments inside the Sustainable Balanced mandate's binding exclusions with no
waiver in the RM notes. CL-0003 scores higher (95) but has no override, so she
ranks second — Critical sorts first by rule.

## Regression stories, all asserted at full precision

**Hartono CL-0001.** CF-0005 is SGD against a 70% trigger. Loan-to-value was
78.50% at 2025-12-31 and 75.68% at 2026-02-27, resolved to 58.86% at
2026-03-31, and is 59.15% today. Drawn stayed SGD 8,000,000 at every snapshot;
current collateral is SGD 26,618,144.28 and lending value SGD 13,525,392.14. The
case status is `historical-resolved` and never `active`. The cure is attributed
to a higher lending value with unchanged borrowing, with the durability caveat
attached. Energy exposure is 41.42% direct plus the declared underlying of the
shipping-and-energy FCN, 44.99% combined, with look-through limits stated. The
SGD 9m 2027 property need and the family constraint on the legacy stake are both
surfaced. Stress scenarios: base 59.15%, and −15% collateral giving 69.59% LTV,
0.41 points from the trigger, `near`.

**Cheung CL-0012.** Wealth fell from USD 30,130,861.79 to USD 28,028,704.71. The
USD 1.1m objective and the USD 1,280,000 planned obligation are both reported as
an Evidence Conflict; Confidence drops to Medium and neither figure is chosen.
The 2045 Treasury maturity, the increased medical drawdown and the refusal to
sell at a loss are all present. A test asserts the case makes no life-expectancy
claim. Traditional Chinese draft passes figure and citation parity.

**Margarethe CL-0003.** Conservative profile (risk tolerance 2) against 71.46%
equity versus a 30% ceiling and fixed income at 9.15% versus a 45% floor. The
confirmed EUR 3.4m inheritance-tax instalment is 36 days out. German draft
passes parity. A test asserts no bereavement wording enters any scoring factor.

**Supporting stories**, all from general rules with no client allowlist:
CL-0006 gated private credit with the USD 5m tuition and USD 3m capital calls;
CL-0004's unanswered 19 August deposits question (High confidence, explicit
non-reply); CL-0011's fourth succession attempt plus KYC due in 5 days;
CL-0009's repeatedly agreed but unexecuted deployment. Near-trigger facilities
are detected generally and resolve to exactly CL-0002 and CL-0014.

## Two findings the brief should know about

**1. Margarethe's "conflicting totals" are not a conflict.** The brief asks to
preserve a material disagreement between USD 22.18m client/holding totals and
USD 20.31m portfolio records. That disagreement does not exist in the data. All
three sources agree exactly at USD 22,181,135.66; the 20,312,395.29 figure is
the `aum_2026-08-26` column, which is denominated in the portfolio's base
currency. EUR 20,312,395.29 × the supplied 2026-08-26 EURUSD rate of 1.092 is
USD 22,181,135.66 to the cent, and the same holds for all 24 portfolios.

Reporting a material conflict here would have been confident fabrication, so the
engine does the opposite: it detects the apparent gap, states that FX explains
it exactly, and says that comparing the two columns directly would manufacture a
disagreement that does not exist. Margarethe's Confidence stays High because her
evidence really is complete. Her rank is unaffected — she is second on the
suitability mismatch alone. If the intended artefact was something else, this is
the place to check.

**2. CN-007 is genuinely ambiguous, and the engine says so.** CL-0006's
"US university fees, two children" records USD 5,000,000 with recurrence
"Annual instalments" running 2026-09-01 to 2030-09-01. Read literally that is
five instalments totalling USD 25m against total wealth of USD 18.07m. The
engine plans against a single instalment — the smaller, safer reading — and
raises an Evidence Conflict rather than resolving it, which is why CL-0006's
Confidence is Medium. This is worth saying out loud in the presentation.

## Data quality

One issue is reported, at `warning` severity: CL-0002's unlisted holding
`SYN-AL-0308` is carried at a 2025-09-30 valuation against a 2026-08-26
snapshot, a 330-day lag. Private markets report late, so this is treated as a
caveat on precision rather than an error, and it lowers that client's
Confidence.

Everything else reconciles. Referential integrity is clean across all twelve
files, there are no duplicate keys, `quantity × price_local` reproduces
`market_value_local` on all 1,015 rows, holdings sum to portfolio AUM at every
snapshot, and holding prices match `instruments.csv` at every snapshot.

## Remaining uncertainties

- **Scoring calibration is a judgement, not a truth.** The weights in
  `scoring.v1.json` were set from the shape of this 20-client book and produce
  1 Critical / 6 High / 13 Watch. The High threshold of 65 is the single most
  consequential number; moving it moves several clients across a tier boundary.
  It is one file to change and every point remains attributable.
- **Look-through is indicative.** Component weights are not supplied, so a
  worst-of basket's whole notional is counted against each named theme as an
  upper bound. This is stated on every claim that uses it and it lowers
  Confidence.
- **Open Loops are candidates.** Free-text detection is good but not perfect:
  CL-0004 produces two loops from one note where a human might record one. All
  are `confirmationRequired` with an exact quotation attached, which is the
  intended division of labour.
- **Event linkage is deliberately narrow.** Channels such as "Gulf credit" and
  "airlines" match nothing in this book, so no link is emitted rather than a
  plausible-sounding one.
- **Cheung ranks 11th.** That is the honest result: nothing in his situation is
  dated or breached in the way the top of the queue is. The Queue is a
  triage order, not a ranking of which story is most worth telling.

## Attribution

No third-party source code or text was copied, so `THIRD_PARTY_NOTICES.md` is
not required. The Meeting Brief structure follows the checklist described in
`docs/research/open-source-leverage.md` — relationship history, holdings, open
items, relevant context, agenda, draft-only staging, no client-facing send —
but the templates and implementation are original.
