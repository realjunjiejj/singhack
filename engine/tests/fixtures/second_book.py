"""A second, genuinely different client Book.

Meridian Wealth, relationship manager Ingrid Solberg. Four clients, five
portfolios, four snapshot dates, two currencies. None of the SingHacks
identifiers, names, dates, instruments or events appear anywhere.

The Book is generated rather than checked in as CSVs so that every derived
figure is consistent by construction: market values come from quantity and
price, base values from the snapshot's own FX rate, portfolio AUM from the sum
of its holdings, and facility lending values from the collateral portfolio.
A fixture that quietly disagreed with itself would prove nothing.

It exercises the same rules as the demonstration Book through different facts:

* a Conservative client holding far too much equity (band break + mismatch);
* a tobacco holding inside a mandate whose notes declare binding exclusions;
* a facility walking toward its margin-call trigger;
* a confirmed obligation falling due inside the safety-override window;
* an event whose transmission channel is recognised and reaches a holding;
* an event whose channel is not recognised and is reported as unsupported;
* one question the bank has not answered, and one answered in the same note;
* a private fund carried at a stale valuation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RM_ID = "RM-ZH-401"
RM_NAME = "Ingrid Solberg"
RM_DESK = "Alpine desk - Zurich and Geneva booking centres"
DATASET_NAME = "Meridian Wealth demonstration Book"

# Deliberately different from the SingHacks grid, and four rather than five.
SNAPSHOTS = ["2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"]
AS_OF = "2026-03-31"

# USD per one CHF at each snapshot. The dataset quotes CHFUSD directly so the
# Book also proves a pair the SingHacks data does not contain.
CHFUSD = {"2025-06-30": 1.10, "2025-09-30": 1.12, "2025-12-31": 1.15, "2026-03-31": 1.18}

# instrument_id -> (name, asset_class, sub_asset_class, sector, region, ccy,
#                   liquidity_tier, advance_rate, underlying, excluded, conc_limit)
INSTRUMENTS = {
    "MW-I-EQ1": ("Global Equity Index Fund", "Equity", "Developed Market Equity",
                 "Diversified", "Global", "USD", "Daily", 65.0, None, "N", "N"),
    "MW-I-EQ2": ("Helvetia Energy AG", "Equity", "Single Stock", "Energy", "Europe",
                 "CHF", "Daily", 50.0, None, "N", "Y"),
    "MW-I-EQ3": ("Zurich Tech Leaders Fund", "Equity", "Developed Market Equity",
                 "Information Technology", "Europe", "USD", "Daily", 60.0, None, "N", "N"),
    "MW-I-ST1": ("Nordkap Tobacco Holding", "Equity", "Single Stock", "Consumer Staples",
                 "Europe", "USD", "Daily", 50.0, None, "Y", "Y"),
    "MW-I-FI1": ("US Treasury 3.000% due 2041", "Fixed Income", "Government Bond",
                 "Sovereign", "North America", "USD", "Daily", 90.0, None, "N", "N"),
    "MW-I-CM1": ("Physical Gold ETC", "Commodities", "Precious Metals", "Gold",
                 "Global", "USD", "Daily", 70.0, "XAU spot", "N", "N"),
    "MW-I-AL1": ("Alpine Private Credit Fund II", "Alternatives", "Private Credit",
                 "Corporate", "Europe", "USD", "Quarterly Gate", 0.0, None, "N", "N"),
    "MW-I-SP1": ("Autocallable ref. Helvetia Energy AG, 8.00% p.a.", "Structured Products",
                 "Yield Enhancement", "Energy", "Europe", "USD", "Illiquid", 0.0,
                 "Single underlying: Helvetia Energy AG", "N", "Y"),
    "MW-I-CA1": ("USD Call Deposit", "Cash and Equivalents", "Deposit", "Cash",
                 "Global", "USD", "Daily", 90.0, None, "N", "N"),
}

PRICES = {
    "MW-I-EQ1": [100.0, 104.0, 108.0, 112.0],
    "MW-I-EQ2": [50.0, 55.0, 60.0, 72.0],
    "MW-I-EQ3": [300.0, 320.0, 340.0, 310.0],
    "MW-I-ST1": [80.0, 82.0, 85.0, 88.0],
    "MW-I-FI1": [98.0, 96.0, 94.0, 90.0],
    "MW-I-CM1": [200.0, 215.0, 230.0, 250.0],
    "MW-I-AL1": [100.0, 100.0, 101.0, 101.0],
    "MW-I-SP1": [100.0, 102.0, 104.0, 99.0],
    "MW-I-CA1": [1.0, 1.0, 1.0, 1.0],
}

AVG_COST = {
    "MW-I-EQ1": 92.0, "MW-I-EQ2": 44.0, "MW-I-EQ3": 275.0, "MW-I-ST1": 90.0,
    "MW-I-FI1": 101.0, "MW-I-CM1": 180.0, "MW-I-AL1": 100.0, "MW-I-SP1": 100.0,
    "MW-I-CA1": 1.0,
}

# The private fund reports on a lag; this mark is a quarter behind the snapshot.
LAGGED_VALUATION = {"instrument": "MW-I-AL1", "valuation_date": "2025-12-31"}

CLIENTS = [
    {
        "client_id": "MW-C-100", "client_name": "Anselm Roth", "age": 71, "gender": "M",
        "nationality": "Switzerland", "country_of_residence": "Switzerland",
        "tax_domicile": "Switzerland", "booking_centre": "Zurich",
        "base_currency": "CHF", "wealth_band": "HNW",
        "life_stage": "Retired - capital preservation",
        "source_of_wealth": "Inherited - family engineering group",
        "risk_profile": "Conservative", "risk_tolerance_score": 2,
        "investment_horizon_years": 8, "liquidity_needs": "Low",
        "objectives": "Preserve capital in CHF terms; keep the family engineering stake intact",
        "client_since": "2011-04-02", "kyc_review_due": "2026-04-20",
        "pep_status": "No", "reporting_language": "German",
    },
    {
        "client_id": "MW-C-200", "client_name": "Beatriz Alarcon", "age": 48, "gender": "F",
        "nationality": "Spain", "country_of_residence": "Switzerland",
        "tax_domicile": "Spain", "booking_centre": "Geneva",
        "base_currency": "USD", "wealth_band": "HNW",
        "life_stage": "Peak earning years",
        "source_of_wealth": "Entrepreneur - renewable energy engineering",
        "risk_profile": "Balanced", "risk_tolerance_score": 5,
        "investment_horizon_years": 18, "liquidity_needs": "Medium",
        "objectives": "Grow capital while respecting the sustainability policy adopted in 2023",
        "client_since": "2016-09-15", "kyc_review_due": "2026-11-01",
        "pep_status": "No", "reporting_language": "English",
    },
    {
        "client_id": "MW-C-300", "client_name": "Cyrus Danesh", "age": 39, "gender": "M",
        "nationality": "Canada", "country_of_residence": "Switzerland",
        "tax_domicile": "Canada", "booking_centre": "Geneva",
        "base_currency": "USD", "wealth_band": "HNW",
        "life_stage": "Pre-liquidity event",
        "source_of_wealth": "Entrepreneur - logistics software",
        "risk_profile": "Growth", "risk_tolerance_score": 8,
        "investment_horizon_years": 20, "liquidity_needs": "Low",
        "objectives": "Bridge liquidity until the funding round closes; keep the credit line available",
        "client_since": "2020-02-10", "kyc_review_due": "2026-06-30",
        "pep_status": "No", "reporting_language": "English",
    },
    {
        "client_id": "MW-C-400", "client_name": "Dilnoza Karimova", "age": 63, "gender": "F",
        "nationality": "Uzbekistan", "country_of_residence": "Switzerland",
        "tax_domicile": "Uzbekistan", "booking_centre": "Zurich",
        "base_currency": "USD", "wealth_band": "HNW",
        "life_stage": "Pre-retirement",
        "source_of_wealth": "Executive compensation - retired mining executive",
        "risk_profile": "Income", "risk_tolerance_score": 3,
        "investment_horizon_years": 12, "liquidity_needs": "High",
        "objectives": "Fund a foundation commitment in 2026; then draw a stable income",
        "client_since": "2014-07-21", "kyc_review_due": "2026-04-05",
        "pep_status": "No", "reporting_language": "Uzbek",
    },
]

PORTFOLIOS = [
    ("MW-P-100", "MW-C-100", "Preservation Mandate", "MW-CONS", "Conservative", "Advisory", "CHF"),
    ("MW-P-200", "MW-C-200", "Sustainable Core Mandate", "MW-SUS", "Sustainable Balanced", "Discretionary", "USD"),
    ("MW-P-201", "MW-C-200", "Legacy Custody Account", "MW-SUS", "Sustainable Balanced", "Custody", "USD"),
    ("MW-P-300", "MW-C-300", "Growth Advisory Portfolio", "MW-GROW", "Growth", "Advisory", "USD"),
    ("MW-P-400", "MW-C-400", "Income Mandate", "MW-INC", "Income", "Advisory", "USD"),
]

# mandate_code -> (name, notes, max_single_position_pct, {asset_class: (min, target, max)})
MANDATES = {
    "MW-CONS": ("Conservative", "Capital preservation. Max 10% in any single position.", 10.0, {
        "Cash and Equivalents": (5, 10, 25), "Fixed Income": (45, 60, 75),
        "Equity": (10, 20, 30), "Alternatives": (0, 5, 15),
        "Commodities": (0, 5, 10), "Structured Products": (0, 0, 10)}),
    "MW-SUS": ("Sustainable Balanced",
               "Balanced allocation with binding exclusions: tobacco, thermal coal and "
               "controversial weapons.", 12.0, {
        "Cash and Equivalents": (2, 7, 18), "Fixed Income": (25, 35, 50),
        "Equity": (30, 40, 55), "Alternatives": (0, 10, 20),
        "Commodities": (0, 3, 10), "Structured Products": (0, 5, 15)}),
    "MW-GROW": ("Growth", "Long-horizon capital appreciation.", 15.0, {
        "Cash and Equivalents": (1, 4, 12), "Fixed Income": (5, 12, 25),
        "Equity": (50, 62, 78), "Alternatives": (0, 17, 30),
        "Commodities": (0, 2, 8), "Structured Products": (0, 3, 15)}),
    "MW-INC": ("Income", "Yield generation with moderate capital risk.", 10.0, {
        "Cash and Equivalents": (3, 8, 20), "Fixed Income": (40, 55, 70),
        "Equity": (15, 25, 35), "Alternatives": (0, 7, 15),
        "Commodities": (0, 2, 8), "Structured Products": (0, 3, 12)}),
}

# (portfolio, instrument) -> quantity held at each snapshot.
QUANTITIES = {
    # Conservative client holding far more equity than the mandate allows.
    ("MW-P-100", "MW-I-EQ1"): [30000, 30000, 30000, 30000],
    ("MW-P-100", "MW-I-EQ2"): [20000, 20000, 20000, 20000],
    ("MW-P-100", "MW-I-FI1"): [8000, 8000, 8000, 8000],
    ("MW-P-100", "MW-I-CA1"): [400000, 400000, 400000, 400000],
    # Sustainable mandate carrying an excluded tobacco holding.
    ("MW-P-200", "MW-I-EQ1"): [24000, 24000, 24000, 24000],
    ("MW-P-200", "MW-I-ST1"): [9000, 9000, 9000, 9000],
    ("MW-P-200", "MW-I-FI1"): [22000, 22000, 22000, 22000],
    ("MW-P-200", "MW-I-CA1"): [600000, 600000, 600000, 600000],
    ("MW-P-201", "MW-I-EQ3"): [3000, 3000, 3000, 3000],
    # Growth client with a facility and a structured note on the energy name.
    ("MW-P-300", "MW-I-EQ3"): [14000, 14000, 14000, 14000],
    ("MW-P-300", "MW-I-EQ2"): [30000, 30000, 30000, 30000],
    ("MW-P-300", "MW-I-SP1"): [12000, 12000, 12000, 12000],
    ("MW-P-300", "MW-I-CA1"): [250000, 250000, 250000, 250000],
    # Income client with the gated, lagged private fund and a near obligation.
    ("MW-P-400", "MW-I-FI1"): [40000, 40000, 40000, 40000],
    ("MW-P-400", "MW-I-CM1"): [4000, 4000, 4000, 4000],
    ("MW-P-400", "MW-I-AL1"): [18000, 18000, 18000, 18000],
    ("MW-P-400", "MW-I-CA1"): [300000, 300000, 300000, 300000],
}

EVENTS = [
    {
        "event_date": "2026-02-10", "event_type": "Market", "region": "Europe",
        "description": "North Sea production outage lifts European energy prices sharply.",
        # "Energy" is a configured transmission channel and reaches a holding.
        "primary_transmission": "Energy, transport", "severity": "High",
    },
    {
        "event_date": "2026-01-20", "event_type": "Policy", "region": "Global",
        "description": "Sovereign wealth funds announce a rebalancing toward domestic infrastructure.",
        # Deliberately not a channel the engine recognises: it must stay unlinked.
        "primary_transmission": "Sovereign wealth flows", "severity": "Medium",
    },
]

NOTES = [
    {
        "note_id": "MW-MEMO-001", "client_id": "MW-C-300", "note_date": "2026-03-10",
        "rm_id": RM_ID, "rm_name": RM_NAME, "channel": "Email",
        "note": "Client asked whether we can raise the facility limit before the funding "
                "round closes. Have not yet replied. Needs a proper conversation about "
                "what the collateral will support.",
    },
    {
        "note_id": "MW-MEMO-002", "client_id": "MW-C-200", "note_date": "2026-02-18",
        "rm_id": RM_ID, "rm_name": RM_NAME, "channel": "Meeting",
        "note": "Client asked why the Nordkap position still sits in the sustainable "
                "mandate. Explained that it predates the 2023 policy and that it is on "
                "the review list.",
    },
    {
        "note_id": "MW-MEMO-003", "client_id": "MW-C-100", "note_date": "2026-01-15",
        "rm_id": RM_ID, "rm_name": RM_NAME, "channel": "Meeting",
        "note": "Annual review in Zurich. Client does not want to sell the family "
                "engineering stake under any circumstances.",
    },
]

CASH_NEEDS = [
    {
        "need_id": "MW-OB-400", "client_id": "MW-C-400",
        "description": "Foundation endowment commitment", "currency": "USD",
        "amount": 1800000, "due_from": "2026-05-15", "due_to": "2026-06-30",
        "recurrence": "One-off", "certainty": "Confirmed",
    },
]

COMMITMENTS = [
    {
        "commitment_id": "MW-PL-400", "client_id": "MW-C-400", "portfolio_id": "MW-P-400",
        "fund_name": "Alpine Private Credit Fund II", "currency": "USD",
        "committed": 3000000, "called_to_date": 1800000, "uncalled": 1200000,
        "expected_call_window": "2026 Q3 to 2027 Q2",
    },
]

FACILITY_TRIGGER = 70.0
# LTV walks toward the trigger without crossing it: near, not active.
FACILITY_TARGET_LTV = {"2025-06-30": 52.0, "2025-09-30": 58.0,
                       "2025-12-31": 63.0, "2026-03-31": 68.4}


def _usd_rate(currency: str, snapshot: str) -> float:
    """USD per one unit of `currency` at `snapshot`."""
    if currency == "USD":
        return 1.0
    if currency == "CHF":
        return CHFUSD[snapshot]
    raise ValueError(f"No rate defined for {currency}")


def _convert(amount: float, from_ccy: str, to_ccy: str, snapshot: str) -> float:
    return amount * _usd_rate(from_ccy, snapshot) / _usd_rate(to_ccy, snapshot)


def _build_holdings() -> pd.DataFrame:
    portfolio_ccy = {row[0]: row[6] for row in PORTFOLIOS}
    portfolio_client = {row[0]: row[1] for row in PORTFOLIOS}
    rows = []
    for index, snapshot in enumerate(SNAPSHOTS):
        for (portfolio_id, instrument_id), quantities in QUANTITIES.items():
            meta = INSTRUMENTS[instrument_id]
            price = PRICES[instrument_id][index]
            quantity = quantities[index]
            local = quantity * price
            base = _convert(local, meta[5], portfolio_ccy[portfolio_id], snapshot)
            usd = _convert(local, meta[5], "USD", snapshot)
            cost_local = quantity * AVG_COST[instrument_id]
            cost_base = _convert(cost_local, meta[5], portfolio_ccy[portfolio_id], snapshot)
            valuation = snapshot
            if instrument_id == LAGGED_VALUATION["instrument"] and snapshot == AS_OF:
                valuation = LAGGED_VALUATION["valuation_date"]
            rows.append({
                "snapshot_date": snapshot,
                "portfolio_id": portfolio_id,
                "client_id": portfolio_client[portfolio_id],
                "instrument_id": instrument_id,
                "instrument_name": meta[0],
                "asset_class": meta[1],
                "sub_asset_class": meta[2],
                "sector": meta[3],
                "region": meta[4],
                "instrument_ccy": meta[5],
                "quantity": quantity,
                "price_local": price,
                "market_value_local": local,
                "portfolio_ccy": portfolio_ccy[portfolio_id],
                "market_value_base": base,
                "market_value_usd": usd,
                "avg_cost_local": AVG_COST[instrument_id],
                "cost_basis_base": cost_base,
                "unrealised_pnl_base": base - cost_base,
                "unrealised_pnl_pct": 100.0 * (base - cost_base) / cost_base if cost_base else 0.0,
                "lending_value_base": base * meta[7] / 100.0,
                "advance_rate_pct": meta[7],
                "liquidity_tier": meta[6],
                "valuation_date": valuation,
                "acquired_date": "2021-03-01",
            })
    frame = pd.DataFrame(rows)
    totals = frame.groupby(["snapshot_date", "portfolio_id"])["market_value_base"].transform("sum")
    frame["weight_pct"] = 100.0 * frame["market_value_base"] / totals
    return frame


def _build_market() -> pd.DataFrame:
    rows = []
    for snapshot in SNAPSHOTS:
        rows.append({"snapshot_date": snapshot, "series_id": "CHFUSD",
                     "series_name": "CHF/USD", "category": "FX",
                     "unit": "USD per CHF", "value": CHFUSD[snapshot]})
        rows.append({"snapshot_date": snapshot, "series_id": "BRENT_USD_BBL",
                     "series_name": "Brent crude", "category": "Commodity",
                     "unit": "USD/barrel", "value": 70.0 + 6 * SNAPSHOTS.index(snapshot)})
        rows.append({"snapshot_date": snapshot, "series_id": "UST_10Y_PCT",
                     "series_name": "US Treasury 10-year yield", "category": "Rates",
                     "unit": "percent", "value": 3.9 + 0.25 * SNAPSHOTS.index(snapshot)})
    return pd.DataFrame(rows)


def write_book(target: Path) -> Path:
    """Write the complete Book to `target` and return the directory."""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)

    holdings = _build_holdings()
    holdings.to_csv(target / "holdings.csv", index=False)

    latest = holdings[holdings.snapshot_date == AS_OF]

    portfolio_rows = []
    for portfolio_id, client_id, name, code, mandate_name, service, ccy in PORTFOLIOS:
        row = {
            "portfolio_id": portfolio_id, "client_id": client_id,
            "portfolio_name": name, "mandate_code": code, "mandate_name": mandate_name,
            "service_model": service, "base_currency": ccy,
            "inception_date": "2016-01-01",
            "benchmark": "None - custody only" if service == "Custody" else f"MW {mandate_name} Composite",
        }
        for snapshot in SNAPSHOTS:
            subset = holdings[(holdings.snapshot_date == snapshot)
                              & (holdings.portfolio_id == portfolio_id)]
            row[f"aum_{snapshot}"] = float(subset["market_value_base"].sum())
        row["aum_usd_current"] = float(
            latest[latest.portfolio_id == portfolio_id]["market_value_usd"].sum()
        )
        portfolio_rows.append(row)
    pd.DataFrame(portfolio_rows).to_csv(target / "portfolios.csv", index=False)

    client_rows = []
    for client in CLIENTS:
        row = dict(client)
        row["rm_id"] = RM_ID
        row["rm_name"] = RM_NAME
        row["rm_desk"] = RM_DESK
        row["total_aum_usd"] = float(
            latest[latest.client_id == client["client_id"]]["market_value_usd"].sum()
        )
        client_rows.append(row)
    pd.DataFrame(client_rows).to_csv(target / "clients.csv", index=False)

    instrument_rows = []
    for instrument_id, meta in INSTRUMENTS.items():
        row = {
            "instrument_id": instrument_id, "instrument_name": meta[0],
            "asset_class": meta[1], "sub_asset_class": meta[2], "sector": meta[3],
            "region": meta[4], "currency": meta[5], "liquidity_tier": meta[6],
            "underlying_reference": meta[8], "sustainability_excluded": meta[9],
            "concentration_limit_applies": meta[10],
        }
        for index, snapshot in enumerate(SNAPSHOTS):
            row[f"price_{snapshot}"] = PRICES[instrument_id][index]
        instrument_rows.append(row)
    pd.DataFrame(instrument_rows).to_csv(target / "instruments.csv", index=False)

    mandate_rows = []
    for code, (name, notes, single, bands) in MANDATES.items():
        for asset_class, (low, target_pct, high) in bands.items():
            mandate_rows.append({
                "mandate_code": code, "mandate_name": name, "asset_class": asset_class,
                "min_pct": low, "target_pct": target_pct, "max_pct": high,
                "max_single_position_pct": single, "mandate_notes": notes,
            })
    pd.DataFrame(mandate_rows).to_csv(target / "mandates.csv", index=False)

    facility = {
        "facility_id": "MW-LN-300", "client_id": "MW-C-300",
        "collateral_portfolio_id": "MW-P-300",
        "facility_type": "Lombard Credit Facility", "facility_ccy": "USD",
        "credit_limit": 12000000, "interest_rate_pct": 5.75,
        "margin_call_ltv_pct": FACILITY_TRIGGER,
    }
    for snapshot in SNAPSHOTS:
        subset = holdings[(holdings.snapshot_date == snapshot)
                          & (holdings.portfolio_id == "MW-P-300")]
        collateral = float(subset["market_value_base"].sum())
        lending = float(subset["lending_value_base"].sum())
        drawn = lending * FACILITY_TARGET_LTV[snapshot] / 100.0
        facility[f"drawn_{snapshot}"] = round(drawn, 2)
        facility[f"collateral_market_value_{snapshot}"] = round(collateral, 2)
        facility[f"lending_value_{snapshot}"] = round(lending, 2)
        facility[f"ltv_pct_{snapshot}"] = round(100.0 * drawn / lending, 2)
        facility[f"headroom_{snapshot}"] = round(lending - drawn, 2)
    facility["utilisation_pct_current"] = round(
        100.0 * facility[f"drawn_{AS_OF}"] / facility["credit_limit"], 2
    )
    pd.DataFrame([facility]).to_csv(target / "credit_facilities.csv", index=False)

    pd.DataFrame(COMMITMENTS).to_csv(target / "commitments.csv", index=False)
    pd.DataFrame(CASH_NEEDS).to_csv(target / "planned_cash_needs.csv", index=False)
    _build_market().to_csv(target / "market_context.csv", index=False)
    pd.DataFrame(EVENTS).to_csv(target / "event_log.csv", index=False)

    transactions = pd.DataFrame([{
        "transaction_id": "MW-TX-0001", "trade_date": "2026-02-20",
        "settlement_date": "2026-02-22", "portfolio_id": "MW-P-300",
        "client_id": "MW-C-300", "transaction_type": "Facility Drawdown",
        "instrument_id": None, "instrument_name": None, "quantity": None,
        "price_local": None, "currency": "USD", "amount": -450000.0,
        "narrative": "Drawdown ahead of the funding round.",
    }])
    transactions.to_csv(target / "transactions.csv", index=False)

    with (target / "rm_notes.json").open("w", encoding="utf-8") as handle:
        json.dump(NOTES, handle, indent=2)

    return target


def singhacks_tokens() -> set[str]:
    """Strings that must never appear in this Book's artifact."""
    return {
        "CL-0001", "CL-0003", "CL-0012", "PF-0001", "CF-0005", "SYN-EQ-0001",
        "Priscilla Ong", "RM-SG-014", "Hartono", "Cheung", "Margarethe",
        "Bara Nusantara", "Golden Harbour", "Hormuz", "2026-08-26",
    }
