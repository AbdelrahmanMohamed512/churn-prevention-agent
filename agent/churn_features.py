"""
The two building blocks the saved model is made of.

WHY THIS FILE HAS TO EXIST
--------------------------
When the notebook saved churn_model.pkl, it did not save the *code* of these two
classes. It only saved a note saying "this model is built from a thing called
ChurnFeatures and a thing called ClipExtremes".

So anything that opens that file has to already know what those two things are.
In Colab they were defined in the notebook. Here, they live in this file.

DO NOT EDIT THESE CLASSES.
They must stay character-for-character identical to the notebook, because the
saved model's numbers were produced by exactly this code. Changing anything here
changes what the model does, silently, with nothing to warn you.

Copied from notebooks/churn_analysis.ipynb, Phase 2, Steps 6 and 7.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

PURCHASE = [f"purchase_month_{i}" for i in range(1, 7)]
PAYMENT  = [f"payment_month_{i}" for i in range(1, 7)]
MONTHS   = np.array([1, 2, 3, 4, 5, 6])

PARTNERS = ["relationship_depth", "payment_ratio", "purchase_volatility",
            "missed_loan_payment_ever", "recent_purchases", "responsibility",
            "spend_to_salary", "has_other_credit_cards",
            "salary_lands_in_bank", "iscore", "borrowing_rate"]

NEVER_USED = (["customer_id", "gender", "churned", "is_paying_old_loan",
               "slope_band", "purchase_pct_change", "payment_slope"] + PAYMENT)


class ChurnFeatures(BaseEstimator, TransformerMixin):
    """Raw bank table in, model-ready numbers out.

    partners : which columns get crossed with the spending trend.
    """

    def __init__(self, partners=None):
        self.partners = partners

    def _base(self, X):
        d = X.copy()
        d["purchase_slope"]      = d[PURCHASE].apply(
            lambda r: np.polyfit(MONTHS, r.values, 1)[0], axis=1)
        d["recent_purchases"]    = d[PURCHASE[3:]].mean(axis=1)
        d["purchase_volatility"] = d[PURCHASE].std(axis=1) / d[PURCHASE].mean(axis=1)
        d["payment_ratio"]       = d[PAYMENT].sum(axis=1) / d[PURCHASE].sum(axis=1)
        d["spend_to_salary"]     = d[PURCHASE].mean(axis=1) / d["salary"]
        d["loan_burden"]         = d["outstanding_loan_balance"] / d["salary"]
        d["responsibility"]      = d["married"] + d["has_dependents"]
        d["borrowing_rate"]      = d["number_of_loans"] / (d["loyalty_years"] + 1)
        d["relationship_depth"]  = (d["salary_lands_in_bank"]
                                    + (1 - d["has_other_credit_cards"])
                                    + (1 - d["missed_loan_payment_ever"]))
        return pd.get_dummies(d, columns=["employment_sector"], prefix="sector")

    def fit(self, X, y=None):
        self.partners_ = list(self.partners) if self.partners is not None else list(PARTNERS)
        d = self._base(X)
        # where every training customer sits, so a rank means the same thing later
        self.rank_ref_ = {c: np.sort(d[c].values.astype(float))
                          for c in ["purchase_slope"] + self.partners_}
        self.columns_ = [c for c in self._interactions(d).columns if c not in NEVER_USED]
        return self

    def transform(self, X):
        d = self._interactions(self._base(X))
        return d.reindex(columns=self.columns_, fill_value=0).astype(float)

    def _interactions(self, d):
        if not hasattr(self, "rank_ref_"):
            return d
        slope_rank = self._pct(d["purchase_slope"], "purchase_slope")
        for p in self.partners_:
            d["slope_x_" + p] = slope_rank * self._pct(d[p], p)
        return d

    def _pct(self, values, column):
        ref = self.rank_ref_[column]
        return np.searchsorted(ref, np.asarray(values, dtype=float), side="right") / len(ref)


class ClipExtremes(BaseEstimator, TransformerMixin):
    """Clip every column to its own 1st and 99th percentile, learned from training data only."""

    def __init__(self, lower=0.01, upper=0.99):
        self.lower, self.upper = lower, upper

    def fit(self, X, y=None):
        Xv = np.asarray(X, dtype=float)
        self.low_  = np.quantile(Xv, self.lower, axis=0)
        self.high_ = np.quantile(Xv, self.upper, axis=0)
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.low_, self.high_)


def register_for_unpickling():
    """Make the saved file loadable.

    The model was saved from a notebook, so inside churn_model.pkl the two
    classes are recorded as living in "__main__" - meaning "whatever file is
    being run right now". So we have to put them there.

    THE CATCH, and why this must be called late.

    "__main__" is a different module depending on how the program was started.
    Run tool.py and it is tool.py. Run agent.py and it is agent.py. Run it under
    Streamlit and it is the Streamlit script - and that module does not even
    exist yet while our imports are happening.

    So this must be called immediately before joblib.load, not once at import
    time. Calling it early was the bug: it wrote the classes into whichever
    module happened to be __main__ at that moment, which was not the one pickle
    looked in afterwards.
    """
    import sys

    targets = [sys.modules.get("__main__")]

    # Streamlit runs the page under its own module name, so cover that too.
    for name, module in list(sys.modules.items()):
        if name.startswith("__main__") or name.endswith("chat") or name.endswith("agent"):
            targets.append(module)

    for module in targets:
        if module is None:
            continue
        module.ChurnFeatures = ChurnFeatures
        module.ClipExtremes = ClipExtremes
        module.PURCHASE = PURCHASE
        module.PAYMENT = PAYMENT
        module.MONTHS = MONTHS
        module.PARTNERS = PARTNERS
        module.NEVER_USED = NEVER_USED
