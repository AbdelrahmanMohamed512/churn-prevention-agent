# Churn analysis: what the field does, and what it means for our data

Research into how people approach bank churn datasets, plus the same methods applied to our own 8,500 rows.

---

# PART 1 — What people actually do

## 1.1 The standard workflow

Almost every serious notebook on bank churn follows the same seven steps. It's worth knowing because deviating from it without a reason looks like inexperience, and following it lets you spend your thinking on the parts that matter.

1. **Understand the business question first.** Not "predict churn" but "who should the retention team call on Monday, and what should they say." Analysis without a decision attached produces charts nobody uses.
2. **Inspect structure and quality.** Rows, columns, types, missing values, duplicates, impossible values.
3. **Look at the target.** How lopsided is it? This one number decides your metrics and your training approach.
4. **Univariate, then bivariate, then multivariate.** One variable alone, then each variable against churn, then variables against each other.
5. **Segment.** Churn rate broken down by group. This is where the actionable findings live.
6. **Engineer features**, then model, starting simple.
7. **Explain the model** and write the story down.

## 1.2 What the community argues about

**SMOTE and synthetic oversampling.** The most common disagreement. SMOTE invents artificial minority-class rows to balance the data. It is used constantly in Kaggle notebooks and treated with suspicion by practitioners, especially for churn and fraud, where the warning is that it makes customer data noisier and inflates false positives. It also produces meaningless values for categorical columns — half a marital status.

The practical position: try it, compare honestly, and be ready to say it didn't help. There are two better first moves anyway — `scale_pos_weight` in XGBoost, which reweights the minority class without inventing data, and simply moving the decision threshold. Both are simpler and neither fabricates customers.

**The one rule nobody disputes:** never resample before splitting. If synthetic rows built from test customers end up in training, your score is fiction.

**Uplift modelling.** The sharpest critique of ordinary churn work, and worth knowing about even though we will not build it. The argument: predicting who *will* leave is not the same as predicting who *can be saved*. Some customers leave whatever you do, and money spent on them is wasted. Worse, "sleeping dogs" are customers who only churn *because* you contacted them — a retention call reminds them they were considering leaving.

Uplift models estimate the change in behaviour caused by the offer, and target only the persuadable. Doing it properly needs data from a controlled experiment where some at-risk customers were treated and some weren't. We have no such data, so we can't build it. But naming it as the honest next step is one of the strongest things we can put in the limitations section — it shows we know the ceiling of what we built.

## 1.3 Performance to expect

Published work on real bank churn data lands roughly at **AUC 0.71 to 0.85**, with F1 often well below 0.6 because of imbalance. One comparative study reported XGBoost at 84.8% accuracy, F1 57%, ROC 71.6% — note how much lower F1 is than accuracy, which is exactly the imbalance trap in one line.

**If you score much above this, suspect yourself before congratulating yourself.**

---

# PART 2 — The traps

Ordered by how likely they are to catch you.

**Leakage is the silent killer.** If a feature secretly contains the answer — an account-closed date, a field only filled in after someone left — the model looks brilliant and is worthless. The rule of thumb from practitioners: a churn model scoring 0.99 is a leakage bug, not a triumph. Ask of every feature: *would this value have been knowable before the customer left?*

**Leakage through preprocessing.** Subtler and very common. Fit a scaler, an imputer, or SMOTE on the whole dataset and information from the test set has already reached your model. Split first, then fit everything on the training set only.

**Accuracy on imbalanced data.** With 20% churners, predicting "nobody leaves" scores 80%. Accuracy is not a metric here, it's a way of hiding.

**No lead time.** A model that flags someone the day they leave is useless. The team needs weeks. This is why the horizon question matters so much.

**Reaching for deep learning.** Neural networks are data-hungry, slow, hard to explain, and lose to gradient boosting on tabular data anyway.

**Charts with no decision attached.** The most common failure in student projects: forty plots, no recommendation. Every chart should answer "so what should we do?"

---

# PART 3 — Our data, analysed with those methods

8,500 rows, 29 columns, no missing values, no duplicates, 20% churned.

## 3.1 The trend is the story

Splitting customers into ten equal groups by purchase trend gives an almost perfectly ordered churn rate:

| Purchase trend | Churn rate |
|---|---|
| -36% (steepest decline) | 64.9% |
| -22% | 38.2% |
| -14% | 27.5% |
| -8% | 20.4% |
| -3% | 13.8% |
| +2% | 11.2% |
| +8% | 8.8% |
| +13% | 6.4% |
| +20% | 6.0% |
| +32% (growing fastest) | 2.5% |

Monotonic from top to bottom, 65% down to 2.5%. Rare and very clean.

And the comparison that justifies feature engineering in one line: **purchase trend correlates with churn at -0.43. Month 1's purchase figure alone correlates at 0.008.** Same twelve columns. The information is entirely in the change, not the level.

## 3.2 The most important caveat about that

**23.5% of churners are not declining.** Roughly one churner in four leaves with stable or rising spending.

This matters more than it looks. It means the trend feature, powerful as it is, is blind to a quarter of the problem, and those customers need the other features to be caught. A weaker analyst finds the strong signal and stops. Ask what the strong signal *misses*.

## 3.3 Interactions — why we chose trees

Churn rate by two features at once:

| | Not declining | Declining |
|---|---|---|
| Never missed a loan payment | 7.6% | 30.5% |
| Has missed one | 13.5% | **52.4%** |

Neither factor alone explains that bottom-right corner. Declining alone takes you to 30%, missing a payment alone to 13.5%, but together it is 52.4%. That is an interaction, and finding it automatically is precisely what tree models do and what logistic regression cannot without being told.

The same pattern with salary deposit:

| | Not declining | Declining |
|---|---|---|
| Salary paid into our bank | 6.6% | 30.4% |
| Salary paid elsewhere | 10.9% | **41.1%** |

## 3.4 The finding with a lever attached

`salary_lands_in_bank` is the strongest static feature: **12.6% churn when salary is deposited with us, 29.1% when it isn't.**

Combined with holding a card elsewhere it becomes sharper still: from 10.2% (salary here, no competing card) to 33.2% (salary elsewhere, competing card). Three times the risk.

What makes this the most valuable thing in the dataset is not the prediction — it's that the bank can *act* on it. Most predictors describe a customer. This one suggests an offer: incentivise the salary transfer. It should be in the catalogue and in the report's recommendations.

## 3.5 Features that predict nothing

**Salary: correlation -0.006.** Not weak — absent. High and low earners leave at identical rates. This quietly disproves the intuition that churn is about affordability. It's about engagement.

**Gender: 19.7% versus 20.2%.** No signal. **Recommendation: drop it.** It adds nothing, and using a protected attribute in a system deciding who receives financial offers is a fairness risk with no upside. Checking and removing it deliberately is a strong paragraph in the report.

## 3.6 Honest concern

The data looks synthetic — no missing values anywhere, no duplicates, unusually regular structure, unusually clean relationships. Real bank extracts are messier.

If so, expect the model to score well above the 0.71–0.85 published range. **That would be a property of the data, not evidence of skill**, and saying so before anyone asks is worth more than the extra points.

---

# PART 4 — How to think like an analyst

The habits that separate an analyst from someone who runs pandas commands.

**Always ask "compared to what?"** "Churners spend 1,239 a month" means nothing. "Churners spend 1,239 while stayers spend 1,793, and the gap opened over six months" is a finding.

**Chase the exception, not the pattern.** The pattern gets you the obvious answer. The exception — a quarter of churners aren't declining — gets you the interesting one.

**Every number needs a denominator.** "1,098 declining customers had missed a payment" is meaningless until you know it's out of 3,472 declining customers.

**Prefer segments to averages.** Averages hide everything. The 12.6% versus 29.1% split is invisible in any overall number.

**Ask what would change the decision.** If a chart wouldn't alter what the marketing team does on Monday, it belongs in an appendix.

**Write the sentence before making the chart.** If you can't say what you expect to see and why it matters, you're decorating rather than analysing.

**Be suspicious of good news.** A great score is more often a bug than a breakthrough. Look for the leak first.

---

# PART 5 — Questions this raises

**For the manager:**

1. Is month 1 the oldest or the most recent? Everything inverts if this is backwards.
2. How long after the six-month window was churn measured?
3. Is this real or generated data?
4. Can the credit limit be included?
5. Was any retention campaign running during this period? If some of these customers were already contacted, the data is contaminated in a way that matters.

**For ourselves during Phase 1:**

- Does any feature encode the outcome? Check each one for knowability before churn.
- Do the results hold in every segment, or only overall?
- What does the strongest feature miss?
- Which findings suggest an action, and which merely describe?

---

# Sources

- Pecan, *Best ML models for churn prediction* — leakage, lead time, imbalance
- Nature Scientific Reports, *Mitigating class imbalance in churn prediction with ensemble methods and SMOTE*
- Towards Data Science, *Use SMOTE with caution*
- ScienceDirect, *Why you should stop predicting customer churn and start using uplift models*
- Medium (bigdatarepublic), *Preventing churn like a bandit* — persuadables and sleeping dogs
- Dean & Francis, *The causes of bank customer churn based on XGBoost and LightGBM*
- Kaggle: Credit Card Customers (BankChurners), Bank Customer Churn Dataset
