"""
Proof that the preprocessing runs inside the agent.

Your manager asked whether the agent does the preprocessing too. It does, and this
file shows it happening rather than claiming it.

Run it:   python agent/check_preprocessing.py
"""

import numpy as np
import pandas as pd

from churn_features import register_for_unpickling
from tool import load_model

register_for_unpickling()

CUSTOMER = {
    "customer_id": "CHECK", "gender": "M", "is_paying_old_loan": 1,
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

model = load_model()["model"]
one_row = pd.DataFrame([CUSTOMER])


print("=" * 68)
print("1. WHAT IS INSIDE THE SAVED MODEL")
print("=" * 68)
print("The .pkl file is not just a set of weights. It is a pipeline, and every")
print("step in it runs every time we score a customer.\n")

for i, (name, step) in enumerate(model.steps, start=1):
    print(f"  step {i}: {name:12s} {type(step).__name__}")

print("\n  The last step is the model. Everything above it is preprocessing.")


print("\n" + "=" * 68)
print("2. THE SAME CUSTOMER AT EACH STAGE")
print("=" * 68)

print(f"\n  RAW, as the employee typed it   -> {one_row.shape[1]} columns")
print("     purchase_month_1 =", CUSTOMER["purchase_month_1"])
print("     salary           =", CUSTOMER["salary"])

built = model.named_steps["features"].transform(one_row)
print(f"\n  AFTER FEATURE BUILDING          -> {built.shape[1]} columns")
print("     purchase_slope       =", round(float(built["purchase_slope"].iloc[0]), 1))
print("     payment_ratio        =", round(float(built["payment_ratio"].iloc[0]), 3))
print("     purchase_volatility  =", round(float(built["purchase_volatility"].iloc[0]), 3))
print("     (columns the raw file never had - built here, not typed in)")

clipped = model.named_steps["clip"].transform(built)
print("\n  AFTER CLIPPING THE EXTREMES")
print("     any value changed by clipping?",
      "yes" if not np.allclose(clipped, built.values.astype(float)) else "no, this customer is not extreme")

scaled = model[:-1].transform(one_row)[0]
print("\n  AFTER SCALING")
print("     salary as the model sees it =", round(float(scaled[list(built.columns).index("salary")]), 3))
print("     (0 means an average customer, +1 means one standard deviation above)")


print("\n" + "=" * 68)
print("3. THE PART THAT MATTERS MOST")
print("=" * 68)
print("\nThe scaling numbers were learned from the 8,500 TRAINING customers, and")
print("saved inside the file. They are not recalculated from whoever we happen")
print("to be scoring now.\n")

scaler = model.named_steps["scale"]
print("  how many columns the scaler remembers averages for:", len(scaler.mean_))
print("  average salary it remembers from training:", round(float(
    scaler.mean_[list(built.columns).index("salary")])))
print("\n  That number came out of the training data months ago. If we recalculated")
print("  it from one customer, that customer would always look perfectly average")
print("  and the model would be useless.")


print("\n" + "=" * 68)
print("4. THE ANSWER TO GIVE YOUR MANAGER")
print("=" * 68)
print("""
  Yes, the preprocessing runs in the agent - because it is not separate from
  the model. It is saved inside it.

  The bug he is worried about is real and common: preprocess during training,
  forget to preprocess in production, and the model gives wrong answers with
  nothing to warn you. It is called training-serving skew.

  We cannot have that bug here, because there is no separate preprocessing
  code to forget. The pipeline IS the model. One call runs all four steps,
  in the same order, with the same numbers as training.
""")
