"""
The tool. Give it a customer, it tells you everything about them.

Four questions, four functions:

    score()          will they close the card, and why
    yearly_value()   what are they worth to the bank
    kind_of()        is it a money problem or a boredom problem
    assess()         all of the above, plus the offer

Run this file on its own to test it:   python agent/tool.py
"""

import os

import joblib
import pandas as pd

from churn_features import register_for_unpickling
from offers import pick_offer

MODEL_FILE = os.path.join(os.path.dirname(__file__), "..", "models", "churn_model.pkl")


# The four rates the bank must set. PLACEHOLDERS for now.
CUT_OF_SPENDING = 0.018    # what the bank keeps from every purchase
INTEREST_RATE = 0.30       # yearly interest on unpaid balance
LOAN_MARGIN = 0.05         # yearly margin on a loan
DEPOSIT_MARGIN = 0.03      # yearly margin on salary held here

# Our guess at how often an offer actually works. A guess, not a measurement.
CHANCE_OFFER_WORKS = {"distressed": 0.40, "drifting": 0.25}


_LOADED = None


def load_model():
    """Read the trained model from disk, once."""
    global _LOADED
    if _LOADED is not None:
        return _LOADED

    if not os.path.exists(MODEL_FILE):
        raise FileNotFoundError(
            "models/churn_model.pkl is missing. Run the notebook in Colab to make it."
        )

    # Must happen HERE, not at import time. See the note in churn_features.py -
    # "__main__" is a different module depending on how the program was started,
    # and under Streamlit it does not exist yet while imports are running.
    register_for_unpickling()

    _LOADED = joblib.load(MODEL_FILE)
    return _LOADED


# ---------------------------------------------------------------------------
# Cleaning up what the employee typed
#
# The model's own preprocessing is saved inside churn_model.pkl and runs by
# itself. But nothing checks what arrives from the conversation, and two things
# go wrong there:
#
#   1. The language model hands us text. "9000" is not the same as 9000, and
#      arithmetic on text either crashes or does something silly.
#   2. A typo is invisible. A salary of 900 instead of 9000 produces a confident,
#      completely wrong answer.
#
# So this is the agent's own preprocessing step. Ranges are the real minimum and
# maximum found in the 8,500 training customers.
# ---------------------------------------------------------------------------
SENSIBLE = {
    "age": (18, 75),
    "salary": (2000, 70000),
    "iscore": (385, 850),
    "loyalty_years": (0, 33),
    "number_of_loans": (0, 6),
    "outstanding_loan_balance": (0, 230000),
}
YES_OR_NO = ["married", "has_dependents", "salary_lands_in_bank",
             "has_other_credit_cards", "had_loan_ever", "missed_loan_payment_ever"]
MONTHLY = ([f"purchase_month_{i}" for i in range(1, 7)]
           + [f"payment_month_{i}" for i in range(1, 7)])


# The language model answers yes/no questions in words, not numbers. It says
# "Yes", or "true", or sometimes "married". The churn model needs 1 and 0.
MEANS_YES = {"yes", "y", "true", "1", "1.0", "married", "has", "does"}
MEANS_NO = {"no", "n", "false", "0", "0.0", "none", "never", "single"}


def clean_customer(customer):
    """Turn text into numbers and complain about anything impossible.

    Returns (cleaned customer, list of problems). An empty list means it is fine.
    """
    clean = dict(customer)
    problems = []

    # 1. yes/no words into 1 and 0
    for field in YES_OR_NO:
        if field in clean and isinstance(clean[field], str):
            word = clean[field].strip().lower()
            if word in MEANS_YES:
                clean[field] = 1.0
            elif word in MEANS_NO:
                clean[field] = 0.0

    # 2. text to numbers
    for field in list(SENSIBLE) + YES_OR_NO + MONTHLY:
        if field in clean:
            try:
                clean[field] = float(clean[field])
            except (TypeError, ValueError):
                problems.append(f"{field} is not a number: {clean[field]!r}")

    # 2. is each value possible?
    for field, (low, high) in SENSIBLE.items():
        if field in clean and isinstance(clean[field], float):
            if not low <= clean[field] <= high:
                problems.append(
                    f"{field} is {clean[field]:.0f}, outside the {low} to {high} "
                    f"range seen in the data. Typo?")

    for field in YES_OR_NO:
        if field in clean and clean[field] not in (0.0, 1.0):
            problems.append(f"{field} should be 0 or 1, not {clean[field]}")

    for field in MONTHLY:
        if field in clean and isinstance(clean[field], float) and clean[field] <= 0:
            problems.append(f"{field} is {clean[field]:.0f}. Monthly figures are "
                            f"never zero in this data.")

    # 3. one cross-check: nobody joins the bank before turning 18
    if "age" in clean and "loyalty_years" in clean:
        if clean["loyalty_years"] > clean["age"] - 18:
            problems.append(
                f"{clean['loyalty_years']:.0f} years with the bank but only "
                f"{clean['age']:.0f} years old. One of those is wrong.")

    return clean, problems


# ---------------------------------------------------------------------------
def score(customer):
    """Will they close the card? Returns the risk and the top three reasons."""
    saved = load_model()
    model = saved["model"]

    one_row = pd.DataFrame([customer])
    risk = float(model.predict_proba(one_row)[0, 1])

    # WHY. The model is a weighted sum: every fact is multiplied by a weight and
    # added up. So the reason a customer scored high is just that list of
    # multiplications, biggest first.
    prepared = model[:-1].transform(one_row)[0]
    weights = model[-1].coef_[0]
    names = model.named_steps["features"].columns_

    effects = prepared * weights
    biggest = sorted(range(len(effects)), key=lambda i: effects[i], reverse=True)

    reasons = []
    for i in biggest[:3]:
        high_or_low = "high" if prepared[i] > 0 else "low"
        reasons.append(f"their {names[i]} is {high_or_low}")

    return risk, saved["threshold"], reasons


# ---------------------------------------------------------------------------
def yearly_value(customer):
    """What is this customer worth to the bank per year, in EGP?

    Four ways the bank makes money from a card customer, added together.
    """
    purchases = [customer[f"purchase_month_{i}"] for i in range(1, 7)]
    payments = [customer[f"payment_month_{i}"] for i in range(1, 7)]

    spent_per_year = sum(purchases) * 2                 # six months doubled
    share_paid_back = sum(payments) / sum(purchases)
    unpaid = spent_per_year * (1 - share_paid_back)

    from_spending = spent_per_year * CUT_OF_SPENDING
    from_interest = unpaid * INTEREST_RATE
    from_loan = customer["outstanding_loan_balance"] * LOAN_MARGIN
    from_salary = 0
    if customer["salary_lands_in_bank"] == 1:
        from_salary = customer["salary"] * 12 * DEPOSIT_MARGIN

    return round(from_spending + from_interest + from_loan + from_salary)


# ---------------------------------------------------------------------------
def kind_of(customer):
    """A money problem, or a boredom problem?

    This decides which offers are even allowed. Asking a struggling customer to
    spend more would be the wrong offer, and possibly a harmful one.
    """
    purchases = [customer[f"purchase_month_{i}"] for i in range(1, 7)]
    payments = [customer[f"payment_month_{i}"] for i in range(1, 7)]
    share_paid_back = sum(payments) / sum(purchases)

    struggling = (share_paid_back < 0.80
                  or customer["missed_loan_payment_ever"] == 1
                  or customer["outstanding_loan_balance"] > 8000)

    return "distressed" if struggling else "drifting"


# ---------------------------------------------------------------------------
def assess(customer):
    """Everything about one customer, in one dictionary."""

    # The agent's own preprocessing: text to numbers, and catch typos.
    # If something is impossible we stop here rather than answer confidently
    # with a wrong number.
    customer, problems = clean_customer(customer)
    if problems:
        return {"problems": problems,
                "message": "Check these details before I can give you an answer."}

    risk, threshold, reasons = score(customer)
    value = yearly_value(customer)
    kind = kind_of(customer)
    offer = pick_offer(customer, kind, value)

    # Is the offer worth making?
    # We gain (risk x chance it works x value). We pay the cost.
    chance = CHANCE_OFFER_WORKS[kind]
    expected_gain = risk * chance * value
    worth_it = expected_gain > offer["cost"]

    return {
        "risk_out_of_100": round(risk * 100),
        "acting_line": round(threshold * 100),
        "will_close": risk >= threshold,
        "reasons": reasons,
        "worth_per_year": value,
        "customer_kind": kind,
        "offer": offer["name"],
        "offer_fixes": offer["fixes"],
        "offer_cost": offer["cost"],
        "expected_gain": round(expected_gain),
        "make_the_offer": worth_it and risk >= threshold,
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_customer = {
        "customer_id": "TEST", "gender": "M", "is_paying_old_loan": 1,
        "age": 39, "married": 1, "has_dependents": 1,
        "employment_sector": "Private", "salary": 9000,
        "salary_lands_in_bank": 0, "loyalty_years": 4.4, "iscore": 640,
        "has_other_credit_cards": 1, "had_loan_ever": 1, "number_of_loans": 2,
        "outstanding_loan_balance": 11610, "missed_loan_payment_ever": 1,
        "purchase_month_1": 2400, "purchase_month_2": 2250, "purchase_month_3": 2100,
        "purchase_month_4": 1850, "purchase_month_5": 1700, "purchase_month_6": 1600,
        "payment_month_1": 1850, "payment_month_2": 1700, "payment_month_3": 1600,
        "payment_month_4": 1400, "payment_month_5": 1300, "payment_month_6": 1200,
    }

    result = assess(test_customer)

    for question, answer in result.items():
        print(f"{question:20s} {answer}")
