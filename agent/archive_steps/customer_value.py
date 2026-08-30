"""
Phase 4 — is this customer worth a retention offer?

WHAT THIS FILE DOES
-------------------
The model answers "will they close the card?". It says nothing about whether we
should spend money stopping them. This file answers that second question.

Three numbers go in:
    risk        - from the model, between 0 and 1
    value       - what this customer is worth to the bank in a year
    saveability - how likely an offer is to change their mind

An offer is worth making when   risk x saveability x value  >  the cost of the offer.

WHY IT IS A SEPARATE FILE
-------------------------
Inside the riskiest fifth of the book, annual customer value runs from about
806 EGP to about 6,856 EGP. Same risk score, eight and a half times the worth.
Treating them alike is how a retention budget disappears.

Run it on its own to see the numbers:
    python agent/customer_value.py
"""

import json
import os

# ---------------------------------------------------------------------------
# THE FOUR RATES THE BANK MUST SET
#
# These are PLACEHOLDERS. Every value figure in the report moves with them.
# They live here, together, so the manager changes four numbers in one place.
# ---------------------------------------------------------------------------
INTERCHANGE_RATE = 0.018   # bank's cut of everything spent on the card
CARD_INTEREST    = 0.30    # yearly interest on a carried balance
LOAN_MARGIN      = 0.05    # bank's yearly margin on an outstanding loan
DEPOSIT_MARGIN   = 0.03    # bank's yearly margin on salary held on deposit

# How likely an offer is to work. A JUDGEMENT, not a measurement — see the
# uplift-modelling limitation in the report. Replace with real campaign figures
# the moment the bank has any.
SAVE_RATE = {
    "distressed": 0.40,   # money problem, still banking with us — reachable
    "drifting":   0.25,   # relationship problem, often already holds a rival card
    "invisible":  0.10,   # flagged, but shows none of the usual signs
}


# ---------------------------------------------------------------------------
# 1. What is this customer worth in a year?
# ---------------------------------------------------------------------------
def annual_value(customer: dict) -> dict:
    """Four revenue lines, all from columns we already have.

    customer: a dict of the raw fields, e.g. purchase_month_1 ... salary.
    Returns each line separately so the agent can explain the total.
    """
    purchases = [customer[f"purchase_month_{i}"] for i in range(1, 7)]
    payments  = [customer[f"payment_month_{i}"] for i in range(1, 7)]

    # six months doubled = a year
    annual_spend = sum(purchases) * 2

    # how much of their spending they actually pay back
    paid_back = sum(payments) / sum(purchases) if sum(purchases) else 1.0
    carried   = max(annual_spend * (1 - paid_back), 0)

    interchange = annual_spend * INTERCHANGE_RATE
    interest    = carried * CARD_INTEREST
    loan        = customer.get("outstanding_loan_balance", 0) * LOAN_MARGIN
    deposit     = (customer.get("salary_lands_in_bank", 0)
                   * customer.get("salary", 0) * 12 * DEPOSIT_MARGIN)

    return {
        "interchange": round(interchange),
        "card_interest": round(interest),
        "loan_margin": round(loan),
        "deposit_margin": round(deposit),
        "total": round(interchange + interest + loan + deposit),
        "annual_spend": round(annual_spend),
        "payment_ratio": round(paid_back, 3),
        "carried_balance": round(carried),
    }


# ---------------------------------------------------------------------------
# 2. Which kind of churner is this?
# ---------------------------------------------------------------------------
def churner_type(customer: dict, risk: float) -> str:
    """Distressed, drifting, or invisible.

    From the Phase 1 finding: two groups with the same risk score need opposite
    offers. Distressed have a money problem, drifting have a relationship one.
    """
    v = annual_value(customer)

    under_pressure = (
        v["payment_ratio"] < 0.80
        or customer.get("missed_loan_payment_ever", 0) == 1
        or customer.get("outstanding_loan_balance", 0) > 8000
    )

    # spending trend: last three months against the first three
    p = [customer[f"purchase_month_{i}"] for i in range(1, 7)]
    first_half, last_half = sum(p[:3]) / 3, sum(p[3:]) / 3
    falling = last_half < first_half * 0.95

    if under_pressure:
        return "distressed"
    if falling or customer.get("has_other_credit_cards", 0) == 1:
        return "drifting"
    # flagged by the model but showing none of the usual signs
    return "invisible"


# ---------------------------------------------------------------------------
# 3. Is an offer worth making?
# ---------------------------------------------------------------------------
def is_offer_worth_it(customer: dict, risk: float, offer_cost: float) -> dict:
    """The whole decision, with every number shown so it can be argued with."""
    value = annual_value(customer)
    kind  = churner_type(customer, risk)
    save  = SAVE_RATE[kind]

    expected_gain = risk * save * value["total"]

    return {
        "worth_it": expected_gain > offer_cost,
        "expected_gain": round(expected_gain),
        "offer_cost": round(offer_cost),
        "margin": round(expected_gain - offer_cost),
        "risk": round(risk, 3),
        "save_rate_assumed": save,
        "churner_type": kind,
        "annual_value": value["total"],
        "value_breakdown": value,
        "explain": (
            f"{round(risk*100)}% chance of leaving, "
            f"{round(save*100)}% assumed chance an offer works, "
            f"worth {value['total']} EGP a year "
            f"-> expected gain {round(expected_gain)} EGP against a cost of {round(offer_cost)} EGP."
        ),
    }


# ---------------------------------------------------------------------------
# 4. Which offers actually fit this customer?
# ---------------------------------------------------------------------------
def _field(customer, name):
    """Values the conditions refer to, computed on demand."""
    p = [customer[f"purchase_month_{i}"] for i in range(1, 7)]
    if name == "recent_purchases":
        return sum(p[3:]) / 3
    if name == "purchase_slope":
        months = [1, 2, 3, 4, 5, 6]
        mbar = 3.5
        return sum((m - mbar) * v for m, v in zip(months, p)) / sum((m - mbar) ** 2 for m in months)
    if name == "payment_ratio":
        return annual_value(customer)["payment_ratio"]
    if name == "annual_value":
        return annual_value(customer)["total"]
    if name == "responsibility":
        return customer.get("married", 0) + customer.get("has_dependents", 0)
    if name == "spend_to_salary":
        return (sum(p) / 6) / customer["salary"] if customer.get("salary") else 0
    return customer.get(name, 0)


def matching_offers(customer: dict, risk: float = 0.5) -> list:
    """Every offer that fits this customer, cheapest first.

    TWO filters, and the order matters.

    First the churner type. This is the whole point of the Phase 1 finding: a
    distressed customer and a drifting one can have the same risk score and need
    opposite offers. Without this filter the code happily recommends "spend more
    and get a statement credit" to someone drowning in debt — which is the wrong
    offer and arguably a harmful one.

    Then the data conditions on each offer.
    """
    path = os.path.join(os.path.dirname(__file__), "offers.json")
    with open(path, encoding="utf-8") as f:
        catalogue = json.load(f)

    order = catalogue["escalation_rule"]["order"]
    kind = churner_type(customer, risk)
    fits = []

    for offer in catalogue["offers"]:
        # filter 1 — is this offer meant for this kind of customer?
        if offer["churner_type"] not in (kind, "either"):
            continue

        # filter 2 — does the customer meet the offer's data conditions?
        ok = True
        for condition, target in offer["conditions"].items():
            if condition.endswith("_below"):
                ok &= _field(customer, condition[:-6]) < target
            elif condition.endswith("_above"):
                ok &= _field(customer, condition[:-6]) > target
            else:
                ok &= _field(customer, condition) == target
        if ok:
            fits.append(offer)

    # cheapest that addresses the real reason comes first
    fits.sort(key=lambda o: order.index(o["id"]) if o["id"] in order else 99)
    return fits


# ---------------------------------------------------------------------------
# A worked example, so you can see it run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    example = {
        "age": 39, "married": 1, "has_dependents": 1, "salary": 9000,
        "salary_lands_in_bank": 0, "loyalty_years": 4.4, "iscore": 640,
        "has_other_credit_cards": 1, "had_loan_ever": 1, "number_of_loans": 2,
        "outstanding_loan_balance": 11610, "missed_loan_payment_ever": 1,
        "purchase_month_1": 2400, "purchase_month_2": 2250, "purchase_month_3": 2100,
        "purchase_month_4": 1850, "purchase_month_5": 1700, "purchase_month_6": 1600,
        "payment_month_1": 1850, "payment_month_2": 1700, "payment_month_3": 1600,
        "payment_month_4": 1400, "payment_month_5": 1300, "payment_month_6": 1200,
    }
    RISK = 0.62   # pretend the model said this

    print("=" * 62)
    print("WHAT IS THIS CUSTOMER WORTH?")
    print("=" * 62)
    for k, v in annual_value(example).items():
        print(f"  {k:18s} {v}")

    print()
    print("=" * 62)
    print("SHOULD WE MAKE AN OFFER?")
    print("=" * 62)
    offers = matching_offers(example, RISK)
    print(f"  churner type      {churner_type(example, RISK)}")
    print(f"  offers that fit   {len(offers)}")
    print()
    for o in offers:
        cost = o["cost_egp"] if o["cost_egp"] is not None else 500  # placeholder
        d = is_offer_worth_it(example, RISK, cost)
        mark = "YES" if d["worth_it"] else "no "
        print(f"  [{mark}] {o['name']:45s} cost {cost:>5}  gain {d['expected_gain']:>5}")

    print()
    print("  " + is_offer_worth_it(example, RISK, 500)["explain"])
    print()
    print("  Recommended:", offers[0]["name"] if offers else "no offer")


# ---------------------------------------------------------------------------
# WHAT WE GAINED
# ---------------------------------------------------------------------------
# A decision that sits between the model and the money.
#
# The model says who might leave. This says whether stopping them pays, using
# three numbers: measured risk, estimated value, and an assumed save rate that
# is clearly labelled as an assumption rather than dressed up as a measurement.
#
# It also refuses to spend on customers who are not worth it. "No offer" is a
# real answer in the catalogue, because an agent that always has something to
# give will always give something.
# ---------------------------------------------------------------------------
