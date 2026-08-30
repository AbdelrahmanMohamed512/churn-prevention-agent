"""
Phase 4 — Step 2: the tool.

WHAT THIS STEP DOES
-------------------
Builds the one function the agent is allowed to call: predict_churn.

Give it a customer's details, and it returns three things:

    1. will they close the card, and how likely
    2. WHY  - which facts about them pushed the score up, and which pulled it down
    3. whether an offer is worth making, and which offers fit

No language model is involved yet. This is plain Python, and we test it by hand
on an invented customer. If the tool is wrong, the agent built on top of it is
wrong too, so we make sure of it first while there is nothing else in the way.

HOW THE "WHY" WORKS
-------------------
The plan originally said SHAP, because the plan assumed a tree model. It is a
logistic regression, so we do not need SHAP.

A logistic regression is already a weighted sum: it takes each fact about the
customer, multiplies it by a weight it learned, and adds them all up. So the
reason a customer scored high IS the list of those multiplications, largest
first. Not an approximation of the reason - the actual arithmetic the model did.

Simpler than SHAP, exact rather than estimated, and explainable in one sentence.

HOW TO RUN IT
-------------
    python agent/step2_churn_tool.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import joblib
import numpy as np
import pandas as pd

# The saved model is built out of two custom classes. Python has to know what
# they are BEFORE the file is opened, or joblib cannot rebuild the model.
# This line puts them where the saved file expects to find them.
from churn_features import register_for_unpickling
register_for_unpickling()

# our own Phase 4 code from the previous piece of work
from customer_value import annual_value, churner_type, matching_offers, SAVE_RATE

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "churn_model.pkl")

# Loaded once and kept, because reading it from disk every time would be slow.
_BUNDLE = None


def load_model():
    """Read churn_model.pkl once and remember it."""
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "\n\n  models/churn_model.pkl does not exist yet.\n\n"
            "  To make it: open notebooks/churn_analysis.ipynb in Colab, run it\n"
            "  through to the end of Phase 3, and the last cell saves and downloads\n"
            "  churn_model.pkl. Put that file in the models/ folder.\n"
        )

    _BUNDLE = joblib.load(MODEL_PATH)
    return _BUNDLE


# ---------------------------------------------------------------------------
# The tool itself
# ---------------------------------------------------------------------------
def predict_churn(customer: dict) -> dict:
    """Score one customer.

    customer: the raw fields, exactly as they appear in the bank file -
              age, salary, purchase_month_1 ... purchase_month_6, and so on.

    Returns a plain dictionary. Everything in it is meant to be readable out
    loud to a marketing employee.
    """
    bundle = load_model()
    model = bundle["model"]
    threshold = bundle["threshold"]

    # The model was trained on a table, so one customer becomes a one-row table.
    row = pd.DataFrame([customer])

    probability = float(model.predict_proba(row)[0, 1])
    will_close = probability >= threshold

    return {
        "will_close": bool(will_close),
        "probability": round(probability, 3),
        "threshold": round(float(threshold), 3),
        "reasons": explain(model, row),
        "plain_english": (
            f"About {round(probability * 100)} out of 100 customers who look like this "
            f"closed their card. The line for acting is {round(threshold * 100)}, "
            f"so this customer is {'above' if will_close else 'below'} it."
        ),
    }


def explain(model, row, top=6) -> dict:
    """Which facts pushed this customer's score up, and which pulled it down.

    Runs the customer through every step of the pipeline except the final
    decision, then multiplies each prepared value by the weight the model
    learned for it. That product IS the contribution.

    We also report whether the customer sits HIGH or LOW on each fact, because
    the number alone is misleading. A big positive contribution from
    "relationship_depth" does not mean a strong relationship pushed them out -
    it means their relationship is unusually WEAK, and that pushed them out.
    """
    scaled = model[:-1].transform(row)[0]                 # after clipping and scaling
    built = model.named_steps["features"].transform(row)  # before scaling: real values
    weights = model[-1].coef_[0]
    names = model.named_steps["features"].columns_

    contributions = scaled * weights

    def describe(i):
        # scaled value is how far from the average customer they sit
        position = "high" if scaled[i] > 0.4 else "low" if scaled[i] < -0.4 else "average"
        return {
            "fact": names[i],
            "their_value": round(float(built.iloc[0, i]), 2),
            "compared_to_others": position,
            "effect": round(float(contributions[i]), 3),
            "sentence": (f"{names[i]} is {round(float(built.iloc[0, i]), 2)} "
                         f"({position} compared with other customers)"),
        }

    order = np.argsort(contributions)
    pushed_up = [describe(i) for i in order[::-1][:top] if contributions[i] > 0]
    pulled_down = [describe(i) for i in order[:top] if contributions[i] < 0]

    return {"pushed_up": pushed_up, "pulled_down": pulled_down}


# ---------------------------------------------------------------------------
# Prediction plus the money decision, which is what the agent actually needs
# ---------------------------------------------------------------------------
def assess_customer(customer: dict) -> dict:
    """Everything about one customer in a single answer."""
    prediction = predict_churn(customer)
    risk = prediction["probability"]

    value = annual_value(customer)
    kind = churner_type(customer, risk)
    save = SAVE_RATE[kind]
    offers = matching_offers(customer, risk)

    # the cheapest offer that addresses this customer's actual reason
    best = offers[0] if offers else None
    cost = (best["cost_egp"] if best and best["cost_egp"] is not None else 500) if best else 0

    break_even = cost / (risk * save) if risk * save > 0 else float("inf")
    worth_it = value["total"] > break_even

    return {
        "prediction": prediction,
        "annual_value_egp": value["total"],
        "value_breakdown": value,
        "churner_type": kind,
        "assumed_save_rate": save,
        "recommended_offer": best["name"] if best else "no offer",
        # Step 6: carry the offer's own reasoning through, so the agent can say
        # WHY this offer suits THIS customer instead of just naming it.
        "offer_is": best["what_it_is"] if best else "Nothing. Monitor and re-check next month.",
        "offer_fixes": best["addresses"] if best else "Not worth spending money on this customer.",
        "offer_cost_egp": cost,
        "break_even_egp": round(break_even),
        "worth_retaining": bool(worth_it and prediction["will_close"]),
        "offers_that_fit": [o["name"] for o in offers],
        "plain_english": (
            f"Worth {value['total']} EGP a year. This is a {kind} customer, so we assume "
            f"a {round(save*100)}% chance an offer lands. The cheapest offer that fits "
            f"costs {cost} EGP, which needs the customer to be worth more than "
            f"{round(break_even)} EGP a year to pay for itself. "
            f"{'It does.' if worth_it else 'It does not, so make no offer.'}"
        ),
    }


# ---------------------------------------------------------------------------
# Test it by hand, on someone we invented
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

    customer = {
        "customer_id": "TEST-001",
        "age": 39, "gender": "M", "married": 1, "has_dependents": 1,
        "employment_sector": "Private", "salary": 9000,
        "salary_lands_in_bank": 0, "loyalty_years": 4.4, "iscore": 640,
        "has_other_credit_cards": 1, "had_loan_ever": 1, "number_of_loans": 2,
        "is_paying_old_loan": 1, "outstanding_loan_balance": 11610,
        "missed_loan_payment_ever": 1,
        "purchase_month_1": 2400, "purchase_month_2": 2250, "purchase_month_3": 2100,
        "purchase_month_4": 1850, "purchase_month_5": 1700, "purchase_month_6": 1600,
        "payment_month_1": 1850, "payment_month_2": 1700, "payment_month_3": 1600,
        "payment_month_4": 1400, "payment_month_5": 1300, "payment_month_6": 1200,
    }

    try:
        result = assess_customer(customer)
    except FileNotFoundError as e:
        print(e)
        raise SystemExit(1)

    p = result["prediction"]
    print("=" * 66)
    print("WILL THEY CLOSE THE CARD?")
    print("=" * 66)
    print(" ", p["plain_english"])
    print()
    print("  Pushed the score UP:")
    for r in p["reasons"]["pushed_up"]:
        print(f"     +{r['effect']:<6} {r['sentence']}")
    print("  Pulled the score DOWN:")
    for r in p["reasons"]["pulled_down"]:
        print(f"     {r['effect']:<7} {r['sentence']}")

    print()
    print("=" * 66)
    print("ARE THEY WORTH KEEPING?")
    print("=" * 66)
    print(" ", result["plain_english"])
    print()
    print("  Recommended:", result["recommended_offer"])
    print("  Others that fit:", ", ".join(result["offers_that_fit"]) or "none")


# ---------------------------------------------------------------------------
# WHAT WE GAINED FROM STEP 2
# ---------------------------------------------------------------------------
# One function the agent can call, tested by hand before any language model is
# anywhere near it.
#
# It answers all three questions in one place: will they leave, why, and is it
# worth spending money on them. The "why" is exact rather than approximated,
# because for a logistic regression the contribution of each fact is simply its
# value multiplied by its weight.
#
# Everything from here is the language model deciding WHEN to call this and how
# to talk about the answer. The judgement itself lives here, in code we can read.
# ---------------------------------------------------------------------------
