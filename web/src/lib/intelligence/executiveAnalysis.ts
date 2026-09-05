import type { ClientCase } from "@/lib/workbench/types";

export interface ExecutiveInsight {
  clientId: string;
  clientName: string;
  headline: string;
  whatHappened: {
    summary: string;
    metrics: { label: string; value: string }[];
  };
  clientDilemma: {
    tension: string;
    trapSummary: string;
  };
  whatShouldBeDone: {
    title: string;
    detail: string;
  }[];
  conversationScript: {
    opener: string;
    whyItWorks: string;
  };
}

export const DEMO_EXECUTIVE_INSIGHTS: Record<string, ExecutiveInsight> = {
  "CL-0012": {
    clientId: "CL-0012",
    clientName: "Cheung Kwok Wing",
    headline: "Long-Duration Bond Trap vs. Immediate Medical & Lifestyle Drawdowns",
    whatHappened: {
      summary:
        "Client is 71, retired, and drawing USD 1,100,000 a year (with confirmed recorded obligations of USD 1,280,000) from a bond portfolio that took heavy unrealized losses of USD 5,886,179 (portfolio down 6.98% / USD 2.1M overall). Following the energy shock and the Federal Reserve's rate pause at 3.50–3.75%, the 10-year Treasury yield rose toward 4.71%. Over 57% of his wealth sits in duration and rate-sensitive fixed income, including USD 5.82M in US Treasury 2.375% due 2045.",
      metrics: [
        { label: "Client Age & Status", value: "71 · Retired" },
        { label: "Annual Cash Drawdown", value: "USD 1,100,000" },
        { label: "Unrealized FI Losses", value: "-USD 5,886,179" },
        { label: "Longest Bond Maturity", value: "Year 2045 (19 yrs)" },
      ],
    },
    clientDilemma: {
      tension:
        "Marcus told his RM he refuses to sell any bond at a loss and insists on waiting for them to recover to par. However, his longest bond (US Treasury 2.375%) does not mature until 2045—when he will be 90 years old. Waiting 19 years to break even while drawing USD 1.1M to USD 1.28M annually for living and medical care is not a plan he can outlive.",
      trapSummary:
        "Refusing to sell long bonds forces the portfolio to fund living and medical draws from coupon cash and short liquidity. Once short liquidity is depleted, he will be forced into distress selling at even worse valuations.",
    },
    whatShouldBeDone: [
      {
        title: "Front-End Yield Laddering",
        detail:
          "Reallocate coupon inflows and maturing short paper into high-grade 1–3 year instruments yielding 4.8%+, creating a dedicated 3-year medical drawdown reserve without liquidating discounted bonds.",
      },
      {
        title: "Reframe 2045 Treasuries as Legacy Assets",
        detail:
          "Ring-fence the 2045 US Treasuries in his mind and reporting as an estate preservation vehicle for his two children, removing the emotional pressure of expecting them to fund his daily living needs.",
      },
      {
        title: "Leverage the Upcoming KYC Review",
        detail:
          "Use the upcoming KYC review on 2026-10-04 (in 39 days) as the formal governance checkpoint to update his cashflow schedule and document the duration realignment.",
      },
    ],
    conversationScript: {
      opener:
        "“Mr. Cheung, I completely understand your frustration seeing red numbers on high-quality bonds after the energy shock, and I agree we should not fire-sell your 2045 Treasuries at a discount. But waiting 19 years until 2045 to break even doesn't fit your immediate need for USD 1.1M in annual medical and living costs. Let's lock in today's high 4.8% short-term yields for your next 3 years of cashflow so your day-to-day care is 100% guaranteed, and we will let your 2045 bonds sit untouched as a long-term inheritance for your children.”",
      whyItWorks:
        "Validates his objection to selling at a loss, separates immediate medical survival cashflow from legacy inheritance, and introduces mathematical certainty without triggering defensive pushback.",
    },
  },

  "CL-0001": {
    clientId: "CL-0001",
    clientName: "Hartono Wijaya Kusuma",
    headline: "Passive LTV Recovery Masking Energy Concentration & Property Closing",
    whatHappened: {
      summary:
        "Hartono's SGD 8,000,000 credit facility breached its 65% LTV trigger twice (hitting 78.5% and 66.8%) before recovering to 59.15%. However, this recovery was 100% passive—driven entirely by temporary coal and energy price spikes following the Strait of Hormuz conflict rather than debt paydown. Meanwhile, 45.0% of his total bank portfolio remains concentrated in energy, identical to his family's operating coal business.",
      metrics: [
        { label: "Current LTV Buffer", value: "59.15% (Trigger: 65%)" },
        { label: "Energy Concentration", value: "45.0% of Wealth" },
        { label: "Upcoming Commitment", value: "SGD 9,000,000" },
        { label: "Property Due Date", value: "November 2026" },
      ],
    },
    clientDilemma: {
      tension:
        "Hartono feels confident because his LTV is back in the green and he remains bullish on coal. He has an SGD 9,000,000 Bukit Timah property closing approaching, but over 80% of his sellable assets are non-SGD, and family governance strictly forbids selling legacy coal shares (which uncles would interpret as weakness). If energy prices normalize before year-end, collateral values will drop right as he draws cash for the property, triggering an automated margin call.",
      trapSummary:
        "Passive collateral inflation gives a false sense of security. Relying on volatile commodity prices to maintain borrowing capacity while entering a major illiquid property commitment is an extreme hidden risk.",
    },
    whatShouldBeDone: [
      {
        title: "Ring-Fence Property Deposit Today",
        detail:
          "Pre-fund the SGD 9.0M property liquidity now using systematic FX forward hedges while energy commodity valuations and the USD/SGD exchange rate are favorable.",
      },
      {
        title: "Active Facility Deleveraging",
        detail:
          "Use peak energy valuations to trim secondary energy FCNs and pay down the SGD 8M credit facility to under 45% LTV, establishing a resilient margin cushion.",
      },
      {
        title: "Respect Family Governance",
        detail:
          "Keep legacy coal mining shares untouched to protect family optics, while diversifying the remainder into non-correlated global real estate and sovereign income.",
      },
    ],
    conversationScript: {
      opener:
        "“Hartono, congratulations on the recent energy rally—it brought your borrowing ratio back down to a healthy 59%. But because that recovery came entirely from coal price swings rather than paying down debt, your safety margin is paper-thin. You opened this account specifically so your personal wealth wouldn't rise and fall with the family coal mine. With your SGD 9M Bukit Timah property closing approaching and sellable assets mostly in USD, another energy dip could freeze your credit line. Let's lock in the SGD property funds today while energy prices are at their peak, so your family governance stays intact and your property purchase is guaranteed.”",
      whyItWorks:
        "Praises his market gains, reminds him of his own stated objective to decouple from family mine risk, and frames the action around ensuring his high-prestige Bukit Timah property purchase goes smoothly.",
    },
  },

  "CL-0005": {
    clientId: "CL-0005",
    clientName: "Aishah binti Rahman",
    headline: "Binding ESG Exclusion Breach & Imminent Australian Tuition Deadline",
    whatHappened: {
      summary:
        "In 2024, Aishah adopted a binding Sustainable Balanced mandate with strict negative exclusions on thermal energy and deforestation. Yet, the portfolio holds SGD 5,586,103 in non-compliant assets (Global Energy Transition Fund and legacy family holding Sunrise Palm). Meanwhile, an AUD 1,450,000 university tuition payment for her children in Australia falls due in just 6 days.",
      metrics: [
        { label: "Non-Compliant Holdings", value: "SGD 5,586,103" },
        { label: "Mandate Type", value: "Sustainable Balanced" },
        { label: "Tuition Obligation", value: "AUD 1,450,000" },
        { label: "Payment Due Date", value: "In 6 Days" },
      ],
    },
    clientDilemma: {
      tension:
        "Aishah believes her portfolio is fully aligned with her family sustainability pledge. She treats Sunrise Palm as an untouchable family legacy separate from the mandate. An upcoming audit will flag the breach, but panic-selling during tuition week risks currency friction and family distress.",
      trapSummary:
        "A contractually binding ESG breach creates regulatory and reputational exposure for both client and bank, while an unmanaged FX conversion for tuition risks unnecessary capital loss.",
    },
    whatShouldBeDone: [
      {
        title: "Immediate Tuition Settlement",
        detail: "Execute AUD 1.45M tuition settlement within 48 hours using eligible cash reserves.",
      },
      {
        title: "Segregated Family Custody",
        detail:
          "Transfer legacy Sunrise Palm shares into a segregated non-discretionary custody sleeve so family shares remain intact without tainting the audited ESG mandate.",
      },
      {
        title: "Reinvest in Certified Green Leaders",
        detail: "Switch the energy fund into verified global green taxonomy leaders.",
      },
    ],
    conversationScript: {
      opener:
        "“Datin Aishah, first and foremost, we have already set aside the AUD 1.45M needed for your children's university fees next week so that payment is completely secure. We also want to protect your family's sustainability reputation: our review found that SGD 5.6M of holdings—including the energy fund and legacy Sunrise Palm—conflict with your 2024 ESG charter. Rather than selling your family shares, we propose moving them into a private custody sleeve where they stay untouched, while aligning the rest of the portfolio with your true values.”",
      whyItWorks:
        "Removes immediate maternal panic about tuition fees first, then solves the regulatory ESG breach without threatening her family palm oil heritage.",
    },
  },

  "CL-0003": {
    clientId: "CL-0003",
    clientName: "Margarethe Voss-Brenner",
    headline: "Recently Widowed Conservative Mandate vs. Aggressive Inherited Portfolio",
    whatHappened: {
      summary:
        "Margarethe recently inherited her late husband's EUR 22.2M estate. Stated risk profile is strictly Conservative ('never taken a risk with money; wants safe and boring'). However, the portfolio as transferred is 76.8% concentrated in aggressive equities and complex structured products. A mandatory EUR 3,400,000 German inheritance tax installment falls due before year-end.",
      metrics: [
        { label: "Risk Profile", value: "Conservative (Stated)" },
        { label: "Equities & Structured", value: "76.8% of Wealth" },
        { label: "Inheritance Tax Due", value: "EUR 3,400,000" },
        { label: "Tax Window", value: "Before Year-End" },
      ],
    },
    clientDilemma: {
      tension:
        "Grieving and overwhelmed, she asked to 'make no changes for now' because she does not understand the complex notes her late husband bought. Leaving EUR 22M in volatile high-beta assets leaves her exposed to market drawdowns right before a EUR 3.4M non-negotiable tax bill.",
      trapSummary:
        "Inaction out of grief leaves an elderly conservative widow exposed to aggressive equity drawdowns and structured-product barrier breaks ahead of a massive tax liability.",
    },
    whatShouldBeDone: [
      {
        title: "Ring-Fence Tax Cash Immediately",
        detail: "Carve out EUR 3.4M in short-term German Bunds or cash equivalents to insulate the tax liability.",
      },
      {
        title: "Gentle Phased De-Risking",
        detail: "Gradually unwind complex derivative notes over 6 months into capital-protected sovereign bonds.",
      },
      {
        title: "Frankfurt Estate Support",
        detail: "Coordinate with wealth planners to document valuation discounts for German tax relief.",
      },
    ],
    conversationScript: {
      opener:
        "“Frau Voss-Brenner, we know how exhausting this period has been and how much you want stability. You told us you want your finances to be safe, simple, and predictable. Right now, over three-quarters of your assets are still in the volatile stocks and complex notes your husband traded, and you have a EUR 3.4M inheritance tax payment due before year-end. We don't want you worrying about market news. Let's immediately lock away the EUR 3.4M in safe government paper so your tax bill is covered, and gently move the rest into dependable, capital-protected income that lets you sleep at night.”",
      whyItWorks:
        "Deep emotional resonance, completely strips out financial jargon, solves the terrifying tax problem immediately, and delivers the peace of mind she requested.",
    },
  },

  "CL-0014": {
    clientId: "CL-0014",
    clientName: "Lau Chi Ming",
    headline: "Severe Real Estate Leverage & Razor-Thin 0.59% LTV Watch Band",
    whatHappened: {
      summary:
        "Chi Ming's Lombard LTV sits at 69.41%—just 0.59% away from the hard 70% watch trigger. He recently drew an additional HKD 4,000,000 to meet margin on underwater equity accumulators. His development business, perpetual bonds, and portfolio are 100% leveraged to Hong Kong real estate, while a Mid-Levels redevelopment project requires a HKD 60,000,000 equity injection by mid-2027.",
      metrics: [
        { label: "Current LTV", value: "69.41% (Trigger: 70%)" },
        { label: "Distance to Trigger", value: "0.59% (High Risk)" },
        { label: "Mid-Levels Equity Need", value: "HKD 60,000,000" },
        { label: "Concentration", value: "100% HK Property Bet" },
      ],
    },
    clientDilemma: {
      tension:
        "Chi Ming insists the HK property market will turn and is confident doubling down. But with LTV at 69.4%, a tiny price decline in his collateral will trigger an automated margin call and forced liquidation, freezing his ability to fund the Mid-Levels project.",
      trapSummary:
        "Over-concentration across business, debt, and derivative accumulators creates a domino liquidation risk on a minor market dip.",
    },
    whatShouldBeDone: [
      {
        title: "Widen LTV Cushion",
        detail: "Close underwater accumulators and pledge unencumbered non-property assets to bring LTV below 60%.",
      },
      {
        title: "Mid-Levels Liquidity Roadmap",
        detail: "Produce a realistic liquidity roadmap for the HKD 60M capital call due mid-2027.",
      },
      {
        title: "Perpetual De-Risking",
        detail: "Trim high-duration property perpetuals into short-dated senior instruments.",
      },
    ],
    conversationScript: {
      opener:
        "“Mr. Lau, nobody understands Hong Kong real estate better than you, and we admire your commitment to the Mid-Levels project. But right now, your Lombard facility is sitting at 69.4% LTV—just 59 basis points from mandatory margin intervention. Because your development business, your perpetuals, and your accumulators all share the same property exposure, a small market tremor could force the bank to liquidate your assets at the worst possible time. Let's restructure your credit buffer today so your balance sheet is protected and your HKD 60M Mid-Levels project remains fully on track.”",
      whyItWorks:
        "Respects his industry expertise, frames de-risking as essential protection for his flagship project, and uses clear arithmetic.",
    },
  },

  "CL-0002": {
    clientId: "CL-0002",
    clientName: "Ravi Chandrasekaran",
    headline: "Pre-IPO Secondary Timing vs. Volatile Tech Lombard Utilization",
    whatHappened: {
      summary:
        "Ravi is preparing for a major secondary sale of founder shares in Q4 2026. However, his Lombard facility sits at 73.71% LTV (1.29% below the 75% trigger). He recently drew USD 1.7M to participate in another pre-IPO secondary, expanding debt right when tech collateral is at its most volatile.",
      metrics: [
        { label: "Current LTV", value: "73.71% (Trigger: 75%)" },
        { label: "Secondary Sale Window", value: "Q4 2026" },
        { label: "Recent Drawdown", value: "USD 1,700,000" },
        { label: "Asset Concentration", value: "US & Asia Tech" },
      ],
    },
    clientDilemma: {
      tension:
        "Ravi refuses to trim listed tech shares before his founder secondary, betting that tech will continue to rally. But drawing debt against high-beta tech collateral leaves him vulnerable to a sudden margin call right during institutional due diligence.",
      trapSummary:
        "A margin call in late Q3 would create executive embarrassment and forced liquidation right ahead of his marquee liquidity event.",
    },
    whatShouldBeDone: [
      {
        title: "Freeze Lombard Facility Drawdowns",
        detail: "Cap credit line draws and establish a USD 2M cash cushion.",
      },
      {
        title: "Family Trust Structuring",
        detail: "Prepare the offshore trust entity ahead of the Q4 secondary to lock in valuation discounts.",
      },
    ],
    conversationScript: {
      opener:
        "“Ravi, your Q4 secondary sale is the transformative event you've built towards, and valuations are looking exceptional. But with your Lombard line at 73.7% LTV, a single bad week in tech earnings could trigger a margin call that distracts you right during banker due diligence. Let's put a firm cap on new drawdowns and secure a USD 2M cash buffer today, so you walk into the Q4 secondary with total control and zero margin stress.”",
      whyItWorks:
        "Directly ties risk management to the success of his upcoming founder secondary sale.",
    },
  },

  "CL-0011": {
    clientId: "CL-0011",
    clientName: "Tan Boon Huat",
    headline: "Declining Health, Portfolio Band Drift, and Succession Deadlock",
    whatHappened: {
      summary:
        "Mr. Tan is 78 and in declining health. His managed portfolios show 2 allocation band breaks and wealth fell 6.73%. Four prior attempts to discuss succession have stalled because he asks for 'more time to think.' The bulk of his estate is illiquid Singapore property with no trust structure in place.",
      metrics: [
        { label: "Client Age & Health", value: "78 · Declining" },
        { label: "Heirs", value: "4 Children (2 in biz)" },
        { label: "Succession Attempts", value: "4 Stalled Meetings" },
        { label: "Primary Wealth", value: "Illiquid SG Property" },
      ],
    },
    clientDilemma: {
      tension:
        "Mr. Tan wants to avoid family conflict between the two children working in the business and the two outside. By delaying the decision, he is guaranteeing that if an unexpected event occurs, his estate will be frozen and property will be sold at fire-sale prices.",
      trapSummary:
        "Procrastination under the guise of 'keeping the peace' leaves an illiquid estate vulnerable to probate gridlock and sibling litigation.",
    },
    whatShouldBeDone: [
      {
        title: "Portfolio Band Realignment",
        detail: "Rebalance the managed portfolio back into conservative band limits to preserve lifestyle income.",
      },
      {
        title: "Initiate Wealth Planning Roundtable",
        detail: "Establish a family trust separating commercial operations from passive sibling inheritances.",
      },
    ],
    conversationScript: {
      opener:
        "“Uncle Tan, you have spent a lifetime building this property empire for your family. But with the portfolio drifting and no trust structure in place, the greatest risk to your legacy is leaving your four children to negotiate illiquid assets during a time of grief. Let's bring in our wealth structuring team this week to put a clear family trust in place—ensuring your personal income is protected for life, and your property holdings stay intact for your grandchildren.”",
      whyItWorks:
        "Speaks respectfully to an elder, frames estate planning as protecting his children and life's work, and guarantees his own financial independence.",
    },
  },

  "CL-0004": {
    clientId: "CL-0004",
    clientName: "Chalermchai Suphanburi",
    headline: "Retirement Cashflow Anxiety & Rate Shock Reinvestment Trap",
    whatHappened: {
      summary:
        "Chalermchai is retiring in Q2 2027 and needs USD 1,450,000/year to fund his living costs and family foundation without touching capital. His wealth fell 6.61% due to bond mark-to-market losses following the rate shock. Panicked by seeing 'red numbers,' he asked whether he should move 100% of his wealth into cash deposits.",
      metrics: [
        { label: "Retirement Target", value: "Q2 2027" },
        { label: "Required Annual Income", value: "USD 1,450,000" },
        { label: "Wealth Drawdown", value: "-6.61% (Rate Shock)" },
        { label: "Client Proposal", value: "Move 100% to Deposits" },
      ],
    },
    clientDilemma: {
      tension:
        "Cash deposits feel safe today, but when central banks ease rates, deposit yields will drop to 2%, creating a USD 600,000+ annual income shortfall that forces him to cannibalize his capital.",
      trapSummary:
        "Fleeing temporary mark-to-market bond losses for cash deposits locks in reinvestment failure exactly when retirement begins.",
    },
    whatShouldBeDone: [
      {
        title: "5-Year Fixed Income Ladder",
        detail: "Lock in high 4.8% yields across a 5-year ladder to guarantee USD 1.45M annual retirement income.",
      },
      {
        title: "Educate on Reinvestment Risk",
        detail: "Demonstrate that cash deposits will not sustain his lifestyle once global central bank easing begins.",
      },
    ],
    conversationScript: {
      opener:
        "“Khun Chalermchai, seeing red marks on your bond statement right before retirement is unsettling, and moving everything to bank deposits feels safe. But deposit rates will drop the moment central banks cut rates, which would jeopardize your USD 1.45M annual income goal and force you to eat into your life savings. Instead of cash, let's lock in today's high 4.8% yields with a 5-year fixed income ladder. That guarantees your exact USD 1.45M retirement income every single year, regardless of where the market moves.”",
      whyItWorks:
        "Acknowledges his anxiety about paper losses, exposes the hidden trap of cash deposits, and provides a guaranteed 5-year income solution.",
    },
  },

  "CL-0017": {
    clientId: "CL-0017",
    clientName: "Fong Enterprises Family Office",
    headline: "G2 vs. G3 Generational Friction & Private Credit Liquidity Freeze",
    whatHappened: {
      summary:
        "G3 education disbursement of USD 900,000 falls due in 6 days. Meanwhile, the family's primary private credit manager has gated redemptions for 3 consecutive quarters. G2 elders insist on capital preservation, while G3 members demand increased venture and tech exposure.",
      metrics: [
        { label: "Family Office Size", value: "USD 87.9M Wealth" },
        { label: "G3 Education Draw", value: "USD 900,000 (In 6 Days)" },
        { label: "Private Credit Gate", value: "3 Quarters Frozen" },
        { label: "Generational Split", value: "G2 Safety vs G3 Tech" },
      ],
    },
    clientDilemma: {
      tension:
        "Illiquid private credit gating has thinned operational liquidity, while ideological clashes between generations threaten governance gridlock ahead of the October investment committee.",
      trapSummary:
        "Unaddressed illiquidity and generational discord could cause embarrassing capital call defaults and family office fracture.",
    },
    whatShouldBeDone: [
      {
        title: "Immediate Education Funding",
        detail: "Fund the USD 900k payment from unencumbered short-term sovereign paper.",
      },
      {
        title: "Dual-Bucket Mandate Structure",
        detail: "Establish a formal multi-sleeve agreement separating G2 core wealth from a G3 venture sleeve.",
      },
    ],
    conversationScript: {
      opener:
        "“We have verified the USD 900,000 G3 education disbursement for next week, but our liquidity map reveals that repeated gating in your private credit fund has reduced your operational buffer. With G2 and G3 having different risk philosophies, we should establish a formal dual-bucket mandate before the October investment committee: one preserving core capital, and one dedicated to next-generation innovation.”",
      whyItWorks:
        "Delivers operational security first, then offers a diplomatic institutional structure that resolves family boardroom conflict.",
    },
  },

  "CL-0019": {
    clientId: "CL-0019",
    clientName: "Abdullah Al-Mansoori",
    headline: "Unconscious Correlation: Shipping Operating Risk Replicated in Wealth Portfolio",
    whatHappened: {
      summary:
        "Abdullah opened his Singapore relationship specifically to achieve geographic and sector diversification away from Gulf shipping. However, following the Strait of Hormuz conflict, he subscribed to energy/shipping FCNs—so now 33.2% of his total wealth is exposed to shipping and oil transport.",
      metrics: [
        { label: "Original Goal", value: "Uncorrelated Diversification" },
        { label: "Shipping Exposure", value: "33.2% of Portfolio" },
        { label: "Operating Business", value: "Gulf Marine Services" },
        { label: "Risk Event", value: "Strait Opening Normalization" },
      ],
    },
    clientDilemma: {
      tension:
        "Abdullah's shipping instincts were rewarded during the energy spike, making him feel confident. But if the geopolitical situation normalizes, his operating business revenue and his portfolio will collapse simultaneously.",
      trapSummary:
        "Doubling down on your operating business theme creates catastrophic synchronized drawdown risk during sector normalization.",
    },
    whatShouldBeDone: [
      {
        title: "Harvest FCN Profits",
        detail: "Take profits on mature shipping FCNs while charter rates remain historically elevated.",
      },
      {
        title: "Rebalance to Uncorrelated Assets",
        detail: "Reinvest proceeds into global healthcare, cloud infrastructure, and developed sovereign debt.",
      },
    ],
    conversationScript: {
      opener:
        "“Abdullah, your shipping instincts have paid off handsomely during the recent disruption. But remember the founding purpose of this Singapore account: to protect your family if Gulf logistics faces a downturn. Today, one-third of this portfolio is tied to shipping and energy. If shipping rates normalize, your business and your investments will suffer simultaneously. Let's bank these profits today and rebalance into uncorrelated global assets that truly safeguard your family wealth.”",
      whyItWorks:
        "Validates his trade success, invokes his own founding rationale for opening an offshore account, and eliminates double-jeopardy risk.",
    },
  },
};

/**
 * Returns tailored executive AI advisory insight for a client case,
 * using the rich curated intelligence bank for demo clients or dynamically
 * synthesizing from clientCase facts, signals, and timeline.
 */
export function getExecutiveInsight(clientCase: ClientCase): ExecutiveInsight {
  const existing = DEMO_EXECUTIVE_INSIGHTS[clientCase.clientId];
  if (existing) {
    return existing;
  }

  // Dynamic synthesis for any other client or uploaded custom dataset
  const primarySignal = clientCase.anticipatorySignals[0];
  const primaryMetric = clientCase.timeline[clientCase.timeline.length - 1];
  const firstFact = clientCase.facts[0]?.statement ?? "Client portfolio requires proactive advisory review.";

  return {
    clientId: clientCase.clientId,
    clientName: clientCase.clientName,
    headline: clientCase.conclusion.slice(0, 95) + (clientCase.conclusion.length > 95 ? "..." : ""),
    whatHappened: {
      summary: `${clientCase.conclusion} ${clientCase.whyNow}`,
      metrics: [
        { label: "Urgency Tier", value: `${clientCase.urgency.tier.toUpperCase()} (${clientCase.urgency.score})` },
        { label: "Primary Focus", value: primarySignal?.type ?? "Advisory Strategy" },
        { label: "Confidence", value: `${clientCase.confidence.score}% · ${clientCase.confidence.level}` },
        { label: "Governance Review", value: clientCase.governanceClocks[0]?.summary ?? "Standard Cycle" },
      ],
    },
    clientDilemma: {
      tension: `The client faces a material tension between declared risk tolerance and current portfolio behavior: ${firstFact}`,
      trapSummary: "Failing to address this structural drift will force suboptimal reactive decisions during market stress.",
    },
    whatShouldBeDone: clientCase.meetingBrief.discussionOptions.map((opt, idx) => ({
      title: `Recommended Step ${idx + 1}`,
      detail: opt,
    })),
    conversationScript: {
      opener: `“${clientCase.meetingBrief.openingQuestion}”`,
      whyItWorks: clientCase.meetingBrief.whyItMatters,
    },
  };
}
