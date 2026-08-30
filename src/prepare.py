"""
Turns raw customer data into the columns the model was trained on.

Why this file exists
--------------------
The model is not trained on the raw bank file. It is trained on four columns
we built ourselves, plus the employment sector split into three yes/no columns.

Any customer scored later - a competition file, or one person typed into the
agent - has to be put through exactly the same steps, in exactly the same way.
If the training data and the live data are prepared even slightly differently,
the model gives wrong answers and nothing crashes to warn you.

So there is one function, and it is the only way data reaches the model.

Used in Phase 2 (training), Phase 3 (the competition file) and Phase 4 (the agent).
"""

import numpy as np
import pandas as pd

PURCHASE_COLS = [f"purchase_month_{i}" for i in range(1, 7)]
PAYMENT_COLS = [f"payment_month_{i}" for i in range(1, 7)]
MONTHS = np.array([1, 2, 3, 4, 5, 6])

# Columns that never reach the model, and why.
DROP = [
    "customer_id",           # a different value for every customer, describes nobody
    "gender",                # no signal, and restricted by regulation in credit decisions
    "churned",               # the answer
    "is_paying_old_loan",    # exactly outstanding_loan_balance > 0, proven, zero disagreements
    "slope_band",            # a viewing aid, just purchase_slope cut into groups
    "purchase_pct_change",   # same trend as purchase_slope, built for explaining to people
    "payment_slope",         # a copy of purchase_slope
] + PAYMENT_COLS             # correlate 0.978-0.986 with their purchase month


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Add the four built columns and split employment_sector into yes/no columns.

    Takes the raw bank table. Returns the same table with extra columns.
    Nothing is removed here - removal happens in model_columns().
    """
    d = raw.copy()

    # The direction of spending, as one number per customer.
    # Fits a straight line through the six monthly figures and takes its slope.
    # Negative means falling. Uses all six months so one odd month cannot distort it.
    d["purchase_slope"] = d[PURCHASE_COLS].apply(
        lambda row: np.polyfit(MONTHS, row.values, 1)[0], axis=1
    )

    # How much they are spending now, rather than which direction it is moving.
    # A card already down to small amounts is easy to close.
    d["recent_purchases"] = d[PURCHASE_COLS[3:]].mean(axis=1)

    # How jumpy their spending is, measured against their own average so that
    # a big spender and a small spender are comparable.
    # Falling and jumpy = drifting out of the habit. Growing and jumpy = healthy.
    d["purchase_volatility"] = (
        d[PURCHASE_COLS].std(axis=1) / d[PURCHASE_COLS].mean(axis=1)
    )

    # How much of their spending a customer pays back.
    # Below 1 means they are carrying debt on the card.
    d["payment_ratio"] = d[PAYMENT_COLS].sum(axis=1) / d[PURCHASE_COLS].sum(axis=1)

    # What share of their income runs through the card.
    # Engagement, not wealth - a card carrying 3% of someone's income
    # was never load-bearing; one carrying 40% is woven into how they live.
    d["spend_to_salary"] = d[PURCHASE_COLS].mean(axis=1) / d["salary"]

    # How stretched they are. WEAK - 75% of customers sit at exactly zero,
    # which makes this close to a "has a loan" flag that had_loan_ever
    # already provides. Built and tested; a candidate for removal.
    d["loan_burden"] = d["outstanding_loan_balance"] / d["salary"]

    # How many household commitments are attached to the card. 0, 1 or 2.
    d["responsibility"] = d["married"] + d["has_dependents"]

    # How strong the relationship with the bank is. 0 to 3.
    # Salary arriving here, no card elsewhere, never missed a loan payment.
    d["relationship_depth"] = (
        d["salary_lands_in_bank"]
        + (1 - d["has_other_credit_cards"])
        + (1 - d["missed_loan_payment_ever"])
    )

    # A tree cannot split on a word. One yes/no column per sector, so no
    # false order is implied between Private, Government and Self-Employed.
    d = pd.get_dummies(d, columns=["employment_sector"], prefix="sector")

    return d


def model_columns(prepared: pd.DataFrame) -> list[str]:
    """The list of columns that actually go into the model."""
    return [c for c in prepared.columns if c not in DROP]


def align(prepared: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Force a prepared table to have exactly the training columns, in order.

    Safety catch. If a scoring file happened to contain no self-employed
    customers, get_dummies would not create that column and the table would
    have the wrong shape. This creates any missing column filled with zeros.
    """
    return prepared.reindex(columns=columns, fill_value=0)


def make_submission(customer_ids, predictions, path="submission.csv") -> pd.DataFrame:
    """Write the Kaggle file: one row per customer, id and 0/1.

    customer_id is dropped from the model's inputs but never deleted - it is
    kept aside and attached back here, in the same row order as the predictions.
    """
    submission = pd.DataFrame({
        "customer_id": np.asarray(customer_ids),
        "churned": np.asarray(predictions).astype(int),
    })
    submission.to_csv(path, index=False)
    return submission
