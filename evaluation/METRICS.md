# Evaluation — what the model actually scored

Every number here comes from `docs/EXPERIMENT_LOG.md`, which was written while the
experiments were running. Nothing has been re-run to produce this folder.

Three labels are used throughout, and they matter:

- **MEASURED** — printed by a real run and written into the experiment log.
- **DERIVED** — arithmetic on measured numbers. Correct, but never printed at the time.
- **NOT RECORDED** — we never wrote it down. It is not guessed here.

---

## 1. The headline (MEASURED)

The chosen model is a logistic regression inside a pipeline that builds the engineered
features, clips the 1st and 99th percentiles, then scales. It was judged with five-fold
cross-validation across all 8,500 customers, so every customer was in a held-out fold
exactly once.

- **ROC AUC: 0.8069**
- **F1 on the churn class: 0.5509**
- **Decision threshold: 0.255** (not 0.5 — chosen to maximise F1)
- **Churners caught: 1,098 of 1,697**
- **Churners missed: 599**

Read plainly: out of every 100 customers who closed their card, the model flagged
about 65 of them in advance.

## 2. The numbers we can work out (DERIVED)

Recall is 1,098 divided by 1,697, which is **0.6470**.

F1 is the harmonic mean of precision and recall, so precision can be recovered from the
two measured figures: **precision ≈ 0.4796**. About 48 out of every 100 people the model
flags do go on to close.

From precision and the 1,098 true positives, the model flagged roughly **2,289 customers**
in total, of whom **1,191 were false alarms**. That leaves **5,612 stayers correctly left
alone**.

Accuracy works out to **0.7894**.

**Why accuracy is not the headline.** 6,803 of the 8,500 customers stayed. A model that
predicts "nobody ever closes" scores 80% accuracy and is worth nothing, because it catches
zero churners. That is why accuracy was deliberately never used to judge anything in this
project — it is written here only because it was asked for.

## 3. Every model tried (MEASURED)

**Survey stage — about 30 model families at default settings, single split:**

Logistic regression 0.8085, calibrated classifier 0.8066, linear SVC 0.8065, linear
discriminant 0.8049, nearest centroid 0.7953, random forest 0.7911, CatBoost 0.7890,
XGBoost at defaults 0.7467.

The four best were all linear. That was the first clue.

**Serious stage — five-fold cross-validation:**

XGBoost with modest settings: AUC 0.7921, F1 0.5236.
XGBoost deeper, depth 6 and 800 trees: AUC 0.7756, F1 0.5080 — worse, because it was
memorising.
CatBoost at defaults: AUC 0.7897, F1 0.5380.
XGBoost tuned by random search: AUC 0.8052, F1 0.5436.
Logistic regression, plain and untuned: AUC 0.8002, F1 0.5434.
**Logistic regression, tuned, with interaction terms and clipping: AUC 0.8069, F1 0.5509.**

The simplest model won. A heavily tuned gradient booster never beat an untuned logistic
regression by a meaningful margin.

## 4. The ceiling test (MEASURED)

The most important result in the project.

We took the model's own predicted probabilities and used them to generate fresh labels —
a world where the model is by definition perfect — then scored the model against those
labels. If there were signal left to find, that score would be much higher.

- AUC against regenerated labels: **0.8074**, standard deviation 0.0069 over 20 runs
- AUC actually observed: **0.8069**

They match. The model has already recovered the process that generates the data. **The
ceiling is roughly AUC 0.807 and F1 0.55**, and no better algorithm gets past it. That is
why the modelling question was closed and the effort moved to the agent.

Put in human terms: roughly a third of people who close their card look identical, in this
data, to people who stay. Their reason for leaving is not in any column we have.

## 5. Would more data help? (MEASURED)

Trained on increasing slices: 1,360 customers → AUC 0.759; 2,720 → 0.765; 4,080 → 0.782;
5,440 → 0.780; 6,800 → 0.788.

Still climbing slightly, so more rows would help a little. But going from 1,360 to 6,800 —
five times the data — bought only 0.029 of AUC. Doubling again would not change a decision.

## 6. Is the probability trustworthy? (MEASURED)

Predicted probability against actual closure rate, by decile:

predicted 0.021 → actual 0.032; 0.040 → 0.049; 0.059 → 0.056; 0.083 → 0.075;
0.112 → 0.099; 0.151 → 0.147; 0.203 → 0.178; 0.278 → 0.304; 0.392 → 0.401; 0.657 → 0.655.

Close on every band. When the model says 40%, about 40 out of 100 such customers do close.
This matters more than AUC for the agent, because the whole retention decision multiplies
that probability by money.

## 7. The competition (MEASURED)

Scored on F1 — established by reading the leaderboard, since the rules did not say.

Threshold 0.50 scored 0.40. Threshold 0.23 scored 0.53. Predicting all ones scored 0.32.
Taking the top 420 by risk scored 0.53. The leaderboard leader was at 0.56.

Twelve simulated runs put cross-validated F1 at 0.548 and held-out test F1 at 0.540, with a
standard deviation of 0.024 and a range from 0.517 to 0.591. The gap between 0.53 and 0.56
is inside that noise — it is luck of the split, not a better model.

## 8. What is NOT RECORDED

- **Accuracy as measured at the time** — never printed; the figure above is derived.
- **Precision as measured at the time** — never printed; derived above.
- **True negatives and false positives as measured** — derived above.
- **Per-fold scores** — only the five-fold means were logged.
- **Confidence intervals on AUC** — never computed.
- **A saved ROC curve or precision-recall curve** — never saved to file. The plots in
  `plots/` are drawn from the recorded numbers, not from a stored training run.
- **Yeo-Johnson skew correction results** — the switch exists in the notebook but was
  never actually run.
