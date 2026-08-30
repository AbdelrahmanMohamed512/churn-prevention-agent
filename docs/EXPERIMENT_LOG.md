# Experiment log — every trial, including the failures

Complete record of what was tested, with numbers. Written for the report: the failures matter as much as the successes, because they are the evidence the surviving choices were actually tested.

**All figures are five-fold cross-validation across all 8,500 customers unless stated.** "F1" always means the churn-class F1 at its best threshold, never the weighted average across both classes.

**Noise floor used throughout: differences under 0.005 are treated as noise, decided before running anything.**

---

# 1. Headline result

| | AUC | F1 |
|---|---|---|
| raw file, nothing engineered, logistic | 0.8000 | 0.5353 |
| XGBoost, untuned, on engineered features | 0.7921 | 0.5236 |
| XGBoost, tuned by random search | 0.8052 | 0.5436 |
| **logistic + interactions + clipping (final)** | **0.8069** | **0.5509** |

**The largest single gain came from changing the model family, not from features or tuning.**

---

# 2. Model families

## 2.1 The survey (LazyPredict, ~30 families, default settings, single split)

Only the ROC AUC column is comparable to our own figures — LazyPredict reports F1, precision and recall as weighted averages across both classes, which sit around 0.80 while the churn-class F1 is around 0.53. **Reading that column would have meant optimising the wrong metric.**

| model | ROC AUC |
|---|---|
| LogisticRegression | 0.8085 |
| CalibratedClassifierCV | 0.8066 |
| LinearSVC | 0.8065 |
| LinearDiscriminantAnalysis | 0.8049 |
| NearestCentroid | 0.7953 |
| RandomForestClassifier | 0.7911 |
| CatBoostClassifier | 0.7890 |
| XGBClassifier (defaults) | 0.7467 |

**Four linear models beat the gradient-boosted one.** This is what redirected the project.

## 2.2 Head-to-head, cross-validated

| model | AUC | F1 |
|---|---|---|
| XGBoost (modest settings) | 0.7921 | 0.5236 |
| XGBoost (deeper: depth 6, 800 trees, lr 0.03) | 0.7756 | 0.5080 |
| CatBoost | 0.7897 | 0.5380 |
| XGBoost (tuned, random search) | 0.8052 | 0.5436 |
| Logistic (plain) | 0.8002 | 0.5434 |

**Decision 16 answered: CatBoost is not better.** 0.7900 vs 0.7897 untuned — three ten-thousandths. Its advantage is native handling of text categories; this dataset has one text column with three values.

**The larger model was worse.** Deeper trees lost 0.014 AUC — overfitting, not underfitting.

---

# 3. Blending

Correlation between the tuned logistic and tuned XGBoost predictions: **0.978.**

| share logistic | AUC | F1 |
|---|---|---|
| 0.00 (xgboost only) | 0.8052 | 0.5436 |
| 0.25 | 0.8067 | 0.5463 |
| 0.40 | 0.8072 | 0.5465 |
| 0.50 | 0.8075 | 0.5470 |
| 0.60 | 0.8076 | 0.5480 |
| 0.75 | 0.8076 | 0.5490 |
| **1.00 (logistic only)** | 0.8071 | **0.5501** |

**Blending did not help.** Géron's rule is to prefer models that make *different* types of errors; at r = 0.978 these make the same errors. Pure logistic was chosen.

---

# 4. Feature engineering

## 4.1 What helped

| feature set | AUC | F1 |
|---|---|---|
| plain logistic | 0.8002 | 0.5434 |
| + rank transforms of continuous features | 0.8050 | 0.5472 |
| + spline / hinge basis on curved features | 0.8016 | 0.5399 |
| + rank and hinges together | 0.8032 | 0.5396 |
| **+ interaction terms** | 0.8068 | **0.5489** |
| + rank and interactions | 0.8071 | 0.5480 |

**Only the interaction terms helped.** Splines and hinges made it worse — the relationships are close enough to straight lines that added curvature only fitted noise.

The interactions are the spending trend, as a percentile rank, multiplied by the percentile rank of each of: `relationship_depth`, `payment_ratio`, `purchase_volatility`, `missed_loan_payment_ever`, `recent_purchases`, `responsibility`, `spend_to_salary`, `has_other_credit_cards`, `salary_lands_in_bank`, `iscore`.

## 4.2 Why only some features helped — the important finding

**A linear model can construct any weighted sum of the columns it already has.**

- `purchase_slope` is a fixed weighted sum of the six monthly columns. Coefficient in the final model: **0.054** — near the bottom.
- `recent_purchases` is the average of months 4–6, another weighted sum. Coefficient: **0.025**.

**Both were essentially free to the model already.** What it cannot construct are ratios, squares and products:

- `purchase_volatility` (involves squares) — coefficient **0.361**, the highest in the model
- `slope_x_relationship_depth` (a product) — 0.303
- `slope_x_purchase_volatility` — 0.252
- `slope_x_recent_purchases` — 0.251
- `spend_to_salary`, `payment_ratio` (ratios) — 0.167, 0.067

**Feature engineering for a linear model means building what it cannot derive itself. Nothing else moves the number.**

## 4.3 Thirteen further features, all tested individually

Baseline 0.5509. None reached 0.553.

| feature | AUC | F1 |
|---|---|---|
| min_month | 0.8069 | 0.5514 |
| max_month | 0.8069 | 0.5504 |
| last_over_max | 0.8081 | 0.5506 |
| last_over_first | 0.8091 | 0.5519 |
| last_is_lowest | 0.8074 | 0.5478 |
| peak_position | 0.8070 | 0.5471 |
| trough_position | 0.8069 | 0.5467 |
| biggest_drop | 0.8064 | 0.5505 |
| n_down_months | 0.8067 | 0.5495 |
| last3_slope | 0.8068 | 0.5509 |
| first3_slope | 0.8068 | 0.5514 |
| acceleration | 0.8068 | 0.5514 |
| range_over_mean | 0.8068 | 0.5497 |

Most are weighted sums of columns already present, which is why they added nothing.

## 4.4 All 190 pairwise products, screened against the model's errors

Every pair of 20 candidate features was multiplied and correlated against the residuals — literally asking "what combination explains what the model gets wrong." Top six cross-validated:

| product | AUC | F1 |
|---|---|---|
| recent_purchases × missed_loan_payment_ever | 0.8073 | 0.5504 |
| recent_purchases × has_other_credit_cards | 0.8072 | 0.5504 |
| purchase_volatility × outstanding_loan_balance | 0.8068 | 0.5510 |
| purchase_volatility × loan_burden | 0.8068 | 0.5506 |
| payment_ratio × spend_to_salary | 0.8070 | 0.5517 |
| recent_purchases × purchase_volatility | 0.8071 | 0.5489 |

**None beat the 0.5509 baseline.**

## 4.5 Feature selection

Dropping the weakest features by coefficient magnitude:

| features kept | AUC | F1 |
|---|---|---|
| 39 (all) | 0.8069 | 0.5509 |
| 36 | 0.8071 | 0.5497 |
| 33 | 0.8073 | 0.5494 |
| **30** | 0.8075 | **0.5526** |
| 27 | 0.8078 | 0.5517 |
| 24 | 0.8079 | 0.5500 |
| 21 | 0.8078 | 0.5509 |
| 18 | 0.8077 | 0.5466 |
| 15 | 0.8069 | 0.5477 |

Best gain **+0.0017** — a third of the noise floor. Pruning does not help.

## 4.6 The raw baseline

| what the model saw | AUC | F1 |
|---|---|---|
| raw file, nothing built | 0.8000 | 0.5353 |
| raw, minus gender and the proven duplicate | 0.7991 | 0.5382 |
| raw + outlier clipping | 0.7998 | 0.5376 |
| everything built (39 columns) | 0.8069 | 0.5509 |

**All feature engineering was worth +0.016 on F1.** Raw logistic regression (0.5353) is close to the fully engineered, fully tuned XGBoost (0.5436).

---

# 5. Preprocessing

## 5.1 Outlier handling

| treatment | AUC | F1 |
|---|---|---|
| raw | 0.8068 | 0.5489 |
| **clip at 1st / 99th percentile** | 0.8069 | **0.5509** |
| clip at 5th / 95th | 0.8068 | 0.5487 |
| log of money columns | 0.8084 | 0.5484 |
| log + clip | **0.8085** | 0.5489 |

**Clipping the extreme 1% helped a linear model** (+0.002). It does nothing for trees, which use only order. Clipping harder removed real information.

**The IQR method breaks on `outstanding_loan_balance`:** 75.4% of customers sit at exactly zero, so Q1 = median = Q3 = 0, the IQR is 0, and the upper bound is 0 — flagging every customer with any balance, 2,088 people, as an outlier.

**Outliers are informative, not noise.** Closure rate inside versus outside the IQR-flagged group:

- low `iscore` (26 customers, 385–446) → **54** per 100, against 20 for everyone else
- long `loyalty_years` (380 customers, 13.8–33 years) → **11** per 100
- high `number_of_loans` (27 customers) → **7** per 100

No customer was removed.

## 5.2 Scaling

Required for the linear model, irrelevant for trees. Fitted inside a pipeline on training folds only.

## 5.3 Class imbalance

| weight | AUC | F1 | best cut |
|---|---|---|---|
| 1 (none) | 0.7921 | 0.5236 | 0.26 |
| 2 | 0.7906 | 0.5251 | 0.39 |
| 4 | 0.7898 | 0.5238 | 0.56 |

**F1 moves by 0.0015 across the whole range while the best cut climbs from 0.26 to 0.56.** That is the mechanism visible in numbers: weighting inflates every probability, the threshold rises to compensate, and the same customers get flagged. **Weighting and the threshold are two controls on one lever.**

Not used. SMOTE not used either — it invents customers who are 0.6 married, and applying it before the split leaks test customers into training.

## 5.4 Leakage checks — none found

- 594 of 1,697 leavers (35%) still had salary landing in the bank. If `salary_lands_in_bank` recorded the outcome this would be near zero.
- Zero values anywhere in the twelve monthly columns: **0**. Lowest month-6 purchase among leavers: 55.71.
- 109 leavers had more than 10 years with the bank.

## 5.5 Duplicate columns removed, with proof

- `is_paying_old_loan` equals `outstanding_loan_balance > 0` in **8,500 of 8,500** rows.
- Each `payment_month_N` correlates with `purchase_month_N` at **0.978 to 0.986**. All six removed; `payment_ratio` kept, since it holds the only information the purchase columns do not.

---

# 6. Tuning

Random search, 40 combinations, five folds, following Géron: *"prefer random search over grid search"* and *"treat your data transformation choices as hyperparameters"* — the clipping level was searched alongside the model settings.

**XGBoost: 0.7921 → 0.8052 AUC, 0.5236 → 0.5436 F1.** The second-largest gain in the project, and the manager's suggestion.

**On Adam:** raised by the manager. Adam is a neural-network optimiser that adjusts weights by gradient descent. XGBoost has no weights adjusted that way — it builds trees sequentially, each correcting the last. There is no place to apply it. The tree equivalent is a hyperparameter search, which was run.

---

# 7. How much data would help

Learning curve, AUC against training size:

| customers | AUC |
|---|---|
| 1,360 | 0.759 |
| 2,720 | 0.765 |
| 4,080 | 0.782 |
| 5,440 | 0.780 |
| 6,800 | 0.788 |

Still rising, so the model is not starved — but five times the data bought 0.029. Going from 6,800 to 8,500 is worth roughly +0.005.

---

# 8. Error analysis

At the chosen threshold: **1,098 churners caught, 599 missed.**

Comparing the missed churners to customers who stayed, across all 39 columns, almost every ratio falls between **0.86 and 1.04**.

| | missed churners | caught churners | stayed |
|---|---|---|---|
| `purchase_slope` | **+4.73** | −146.25 | **+22.03** |
| `missed_loan_payment_ever` | **0.08** | 0.51 | **0.11** |
| `purchase_month_6` | 1,668 | 1,005 | 1,793 |
| `relationship_depth` | 2.06 | 1.22 | 2.12 |

**The churners we miss look like customers who stayed.** Their spending is barely declining, and they have a *better* payment record than the average stayer.

Only ratio above 1.10: `sector_Self-Employed` at 1.21 — already elevated among caught churners too, and already used by the model.

**No new feature is hiding in these customers.** They left for reasons not recorded in the file.

---

# 9. The ceiling — demonstrated, not argued

The dataset is synthetic. Evidence gathered independently:

1. Zero missing values, zero duplicate rows
2. Zero contradictions across five cross-column consistency rules
3. Payment-to-purchase ratio identical to three decimal places between the first and second half of the year, for both groups
4. Closure rate 1,697/8,500 = 19.96%, three rows off a round 20%

Synthetic churn data is generated by computing a probability per customer and drawing the outcome at random. That places a hard ceiling on any model, because the draw itself cannot be predicted.

**The test:** take the model's predicted probabilities, discard the real labels, generate fresh random labels from those probabilities, and measure AUC. If the model has recovered the true probability function, the figures match.

- **AUC on regenerated labels: 0.8074** (sd 0.0069, 20 runs)
- **AUC observed: 0.8069**

**They match. The model has recovered the generating process.**

Calibration confirms it:

| predicted | actual |
|---|---|
| 0.021 | 0.032 |
| 0.040 | 0.049 |
| 0.059 | 0.056 |
| 0.083 | 0.075 |
| 0.112 | 0.099 |
| 0.151 | 0.147 |
| 0.203 | 0.178 |
| 0.278 | 0.304 |
| 0.392 | 0.401 |
| 0.657 | 0.655 |

**Ceiling: AUC ≈ 0.807, F1 ≈ 0.55.** Further gains require information never recorded — reason for closure, competitor offers, complaints, branch interactions.

---

# 10. The competition

Scored on **F1** (established from the leaderboard, not from the rules: scores clustered at 0.40–0.56, impossible for accuracy where the floor is 0.80).

## 10.1 Submissions

| submission | score |
|---|---|
| threshold 0.50 (accuracy-optimal) | 0.40 |
| threshold 0.23 (F1-optimal) | **0.53** |
| all ones | 0.32 |
| top 420 by risk | 0.53 |
| leaderboard leader | 0.56 |

## 10.2 Reading the test set from the leaderboard

F1 = 2·TP / (flagged + actual churners). Predicting "everyone churns" makes TP equal the number of churners, leaving one unknown:

**churners = 1500 × 0.32 / (2 − 0.32) = 286**, i.e. **19.1%** of the test set, against 19.96% in training.

Reading the 0.53 submission backwards at 450 flagged: TP = 195, **precision 0.433, recall 0.682.** Far apart — F1 is the harmonic mean and rewards balance, so too many customers were being flagged.

## 10.3 How much of the leaderboard is luck

Simulated the competition 12 times: hold out 1,500 customers, run the full pipeline on the remaining 7,000, apply to the holdout.

- CV F1 averaged **0.548**
- Test F1 averaged **0.540**
- **Standard deviation of the test score: 0.024**
- Range across draws: **0.517 to 0.591** — same model, same code

Transferring the flag *rate* instead of the threshold made no difference (−0.0074 vs −0.0076).

Optimal flag count across 15 draws: **422 of 1,500** (sd 26).

**0.53 and 0.56 are one standard deviation apart. Both are consistent with a true score of about 0.545.**

---

# 11. What was never tried, and why

- **SMOTE** — produces fractional values in yes/no columns; weighting already shown to do nothing
- **Neural networks / Adam** — gradient boosting reliably beats them on tabular data at this size
- **Probability calibration** — does not change ranking, so cannot change F1 at the best threshold
- **KNN as a predictor** — weak on mixed tabular data; the "find similar customers" idea is kept for the agent instead
- **More leaderboard submissions** — with a standard deviation of 0.024, six variations would produce one at 0.57 by luck. Géron: *"Don't tweak your model after measuring the generalization error."*
