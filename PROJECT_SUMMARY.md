# Churn Prevention Agent — Project Summary

An internship project built for a bank's credit card marketing team.

Everything below is taken from work actually done and recorded. Where a number or a fact
was never written down, it says **NOT RECORDED** rather than a guess.

---

## Contents

1. The problem
2. The dataset
3. The machine learning model
4. Feature engineering
5. The agent
6. End to end — what happens when someone uses it
7. Tech stack
8. What was shown, and what came back
9. What this does not do
10. What comes next
11. What is in this package

---

## 1. The problem

A credit card customer closes their card. The bank finds out when it has already happened,
which is the one moment when nothing can be done about it.

**Churn here means the customer closed their credit card.** It does not mean they left the
bank. This distinction was fixed early and held throughout — a customer can close a card
and keep a mortgage, a salary account and a deposit, and those still earn money.

The marketing team wanted two things:

1. Who is about to close, early enough to act.
2. For those people, **is a retention offer actually worth making**, and which one.

The second question is the one that makes this a business tool rather than a model. A
prediction with no decision attached is a number nobody uses.

The work ran in phases. Phases 1 to 3 were the data, the features and the model. Phase 4
was the agent. Phase 5, testing and write-up, **has not started**.

---

## 2. The dataset

**8,500 credit card customers**, one row each, 29 columns. Supplied by the bank for the
project.

**6,803 stayed and 1,697 closed — a closure rate of 19.96%.** Roughly one in five. Not
balanced, but not the extreme imbalance that breaks everything either.

The currency is EGP and one of the columns is an I-Score, which is Egypt's credit bureau
score, running roughly 385 to 850 in this data. The dataset is Egyptian.

What each row holds, in plain terms:

- **Who they are** — age, salary, marital status, number of dependants, years with the bank
  (up to 33), education, job type.
- **What they hold** — number of loans (0 to 6), outstanding loan balance (up to about
  230,000), whether they have a deposit, whether they have a mortgage, credit limit.
- **How they behave** — six months of card spending, six months of repayments, number of
  complaints, number of support calls, whether they use digital banking.
- **Credit standing** — I-Score, missed payments.
- **The answer** — whether the card was closed.

The full column list with dtypes, ranges and category values is in
`data/schema/schema.json`. A five-row **synthetic** sample is in
`data/schema/synthetic_sample_5rows.csv` — those five customers are invented, with
`SYNTH-` ids, to show the shape only.

**No real client data is in this package.** The raw and processed CSVs were excluded and
the package was checked for CSV files before zipping.

---

## 3. The machine learning model

### What was tried, and what it scored

**Stage one — a broad survey.** About 30 model families at default settings on a single
split, to see the landscape:

Logistic regression 0.8085, calibrated classifier 0.8066, linear SVC 0.8065, linear
discriminant 0.8049, nearest centroid 0.7953, random forest 0.7911, CatBoost 0.7890,
XGBoost at defaults 0.7467.

The top four were all linear models. That was the first sign that the relationship in this
data is close to a straight line and there is no hidden structure for a tree ensemble to
find.

**Stage two — five-fold cross-validation, taken seriously:**

| model | AUC | F1 (churn class) |
|---|---|---|
| XGBoost, modest settings | 0.7921 | 0.5236 |
| XGBoost, depth 6, 800 trees | 0.7756 | 0.5080 |
| CatBoost, defaults | 0.7897 | 0.5380 |
| XGBoost, tuned by random search | 0.8052 | 0.5436 |
| Logistic regression, plain and untuned | 0.8002 | 0.5434 |
| **Logistic regression, tuned + interactions + clipping** | **0.8069** | **0.5509** |

The deeper XGBoost scored *worse* than the shallow one — it was memorising the training
rows rather than learning the pattern. And a heavily tuned gradient booster finished
roughly level with a logistic regression that had no tuning at all.

**The simplest model won.** That was not a preference, it was the result.

### The chosen model

Logistic regression inside a scikit-learn `Pipeline`:

```
build engineered features → clip 1st and 99th percentiles → scale → logistic regression
```

- **ROC AUC 0.8069**, five-fold cross-validated on all 8,500 customers
- **F1 on the churn class 0.5509**
- **Decision threshold 0.255**, not 0.5, chosen to maximise F1
- **1,098 churners caught, 599 missed** out of 1,697

Sixty-five out of every hundred people who close are flagged in advance.

Accuracy was **deliberately not used** to judge anything. Predicting "nobody closes" scores
80% and catches nobody. A derived accuracy figure of 0.7894 appears in
`evaluation/METRICS.md` only because completeness was asked for; precision, false positives
and true negatives there are also derived rather than measured, and are labelled as such.

### Why the modelling stopped

This is the most important result in the project.

We generated fresh labels from the model's own predicted probabilities — a world where the
model is perfect by construction — and re-scored against them. If real signal remained
undiscovered, that score would be far higher than the observed one.

- AUC against regenerated labels: **0.8074** (sd 0.0069 over 20 runs)
- AUC actually observed: **0.8069**

They match. The model has already recovered the process that generates this data. **The
ceiling is about AUC 0.807 and F1 0.55.** No algorithm gets past it, because roughly a
third of the people who close look identical, in these 29 columns, to people who stay.
Their reason is not in the data.

That closed the modelling question and moved the whole project to the decision layer.

### Two supporting checks

**Does more data help?** Trained on growing slices: 1,360 rows → 0.759, 2,720 → 0.765,
4,080 → 0.782, 5,440 → 0.780, 6,800 → 0.788. Still rising, but five times the data bought
0.029 of AUC. Doubling again would not change a decision.

**Are the probabilities honest?** Predicted against actual, by decile: 0.021→0.032,
0.040→0.049, 0.059→0.056, 0.083→0.075, 0.112→0.099, 0.151→0.147, 0.203→0.178, 0.278→0.304,
0.392→0.401, 0.657→0.655. Close on every band. This matters more than AUC for the agent,
because the retention decision multiplies that probability by money.

### The competition

The project ran alongside a leaderboard, scored on F1 (established by reading the
leaderboard — the rules did not say). Threshold 0.50 scored 0.40; threshold 0.23 scored
0.53; predicting all ones scored 0.32; taking the top 420 by risk scored 0.53; the leader
sat at 0.56.

Twelve simulated runs put cross-validated F1 at 0.548 and held-out F1 at 0.540, sd 0.024,
range 0.517 to 0.591. **The gap between 0.53 and 0.56 sits inside that noise** — it is the
luck of the split, not a better model.

---

## 4. Feature engineering

Six months of spending and six months of repayments are twelve raw columns that a linear
model can do very little with. The work was turning them into shapes.

**purchase_slope.** A straight line fitted through the six spending months by least squares
— for each candidate line, measure the vertical gap from each of the six points, square it,
add the six squares, keep the line where the total is smallest. `np.polyfit(months, values,
1)[0]`. Squaring removes the sign and punishes one large miss more than several small ones.
Not month six minus month one, which throws away four months and breaks on one odd month.

**purchase_volatility.** How erratic the spending is. This turned out to be the single
strongest input in the whole model.

**payment_ratio.** Repayments against spending — are they clearing the card or carrying it.

**spend_to_salary.** Card spending as a share of income. Strain.

**borrowing_rate.** Added later from previously unused columns, with 2×2 evidence behind
it. Skew measured at 2.94, which is what motivated the clipping step.

**relationship_depth.** How many products the customer holds. A thin relationship is easier
to walk away from.

**Four interaction terms** — the slope multiplied by depth, by volatility, by recent
purchases, and so on. These were the real finding.

### What the coefficients say

Logistic regression is a scorecard: scale each input, multiply by a fixed weight, add. The
weights *are* the explanation, exactly, which is why **no SHAP was needed**. Recorded
absolute standardised coefficients:

purchase_volatility 0.361, slope × relationship_depth 0.303, slope × purchase_volatility
0.252, slope × recent_purchases 0.251, spend_to_salary 0.167, payment_ratio 0.067,
purchase_slope 0.054, recent_purchases 0.025.

**Three of the top four are interactions.** On its own the spending slope scores 0.054 —
nearly nothing. Combined with context it scores 0.303, 0.252 and 0.251. The direction of
spending only means something once you know who it is happening to.

And `recent_purchases` at 0.025 is almost ignored. The *change* matters; the *level* does
not.

### The raw signal underneath

Closures per 100 customers, by how far spending fell over six months: fell more than 30% →
70.0; fell 20–30% → 42.0; fell 10–20% → 28.1; fell 5–10% → 19.1; roughly flat → 13.4;
growing → 6.9. Across the extremes of the slope feature, 48.6 down to 3.9. The strongest
single relationship in the dataset.

### Preprocessing, and one real bug

Logistic regression needs its inputs on comparable scales and is dragged around by extreme
values, so: **clip the 1st and 99th percentiles, then standard-scale.** Both live *inside*
the pipeline, so they cannot be skipped at serving time — the training-serving skew problem
solved structurally rather than by remembering.

**A genuine bug was found and fixed:** percentile ranks were originally being fitted on all
8,500 rows before cross-validation split them. That leaks information from the validation
fold into training and quietly inflates every score. Moved inside the pipeline.

Two ideas were **rejected on evidence**: a `tenure_share` feature that scored worse than
the raw column it was built from, and loan size as a value driver, dropped at the manager's
request. Yeo-Johnson skew correction has a switch in the notebook but **was never actually
run**.

---

## 5. The agent

### Why an agent at all

The model outputs a probability. A marketing employee cannot act on a probability. They
need: is this person about to leave, are they *worth* keeping, and what do we offer them.

The agent is the layer that turns one number into that decision. It runs **locally** — the
manager's instruction was Ollama rather than a cloud API, so no customer detail leaves the
building.

### The pieces

**`agent/tool.py`** — all the thinking, no conversation.

- `load_model` — loads the pickle lazily and caches it
- `clean_customer` — validates and normalises the 25 inputs
- `score` — runs the pipeline, returns the probability
- `yearly_value` — what the customer is worth to the bank per year
- `kind_of` — which type of churner this is
- `assess` — puts it together and returns a structured result

**`agent/offers.py`** — eight real retention offers plus an explicit `NO_OFFER`. Plain
if/else, first matching rule wins, and the `NO_OFFER` check runs **first**: if the customer
is worth less than 800 EGP a year, no offer is made at all.

**`agent/agent.py`** — the conversation. Collects 25 details, decides what is still
missing, decides what to ask next, routes each message, and speaks.

**`agent/churn_features.py`** — a verbatim copy of the notebook's `ChurnFeatures` and
`ClipExtremes` classes so the pickle can be unpickled outside Colab. **This file must never
be edited** — if it drifts from the notebook, the model silently computes different
features.

**`agent/chat.py`** — the Streamlit window. No logic in it at all.

### The two decisions the agent makes

**Decision one: is this person worth an offer?**

Yearly value is built from what the customer actually earns the bank — a cut of card
spending, interest on carried balance, margin on loans, margin on deposits. Then the
break-even rule:

> the customer must be worth more than **cost ÷ (risk × chance the offer works)**

If someone is 40% likely to leave and the offer works 25% of the time, the offer only has a
10% chance of saving anything. It has to be worth more than ten times its cost. This stops
the bank spending 500 EGP to retain someone who earns it 600 a year.

**Decision two: which offer?**

Two churner types were identified, and this is the part the manager engaged with most:

- **Distressed** — a money problem. High spending against salary, missed payments, a
  falling slope because they cannot afford it. They need relief: a payment plan, a fee
  waiver, a rate reduction.
- **Drifting** — a relationship problem. They can afford the card, they have simply stopped
  caring. Thin relationship, low engagement. They need a reason: cashback, a rewards boost,
  a limit increase.

**Same risk score, opposite correct offer.** Sending a hardship plan to a drifting customer
is insulting and sending a rewards boost to a distressed one is useless. The risk model
cannot tell these apart. The agent can, because it looks at the shape of the inputs rather
than the single output number.

The rates driving the arithmetic are **placeholders and are flagged as such in the code**:
1.8% cut of spending, 30% interest, 5% loan margin, 3% deposit margin, and an offer
success chance of 40% for distressed and 25% for drifting. **The real figures are NOT
RECORDED — the bank has not supplied them.** Eight numbers in total are waiting on the
manager, listed in `docs/QUESTIONS_FOR_MANAGER.md`.

### The engineering lesson

Four separate bugs during Phase 4 all had the same root cause: **a 4-billion-parameter
model cannot be trusted with structure.**

It put age and salary into the card-spending slot. It labelled a spending list as
repayments. It stopped calling the tool entirely once it had been given three jobs at once.
It printed its own thinking to the user.

Every fix moved the job **out of the prompt and into plain Python**. Nearest-keyword
matching for which list is which. A comma-run regex for six numbers in a row. A yes/no word
map. A three-route `respond()` function so the tool runs when something new is learned or
when the user asks, and not on every message.

**The result: 18 of the 25 fields are now extracted by our own code with no model
involvement.** The language model is used for what it is good at — talking — and nothing
else.

### Two things the agent will not do

It **will not disclose internal details**. Model accuracy, AUC, F1, the threshold, the
algorithm, file names, how it was trained. Asked how accurate it is, it says only that it
was tested on thousands of the bank's own customers, and that a meaningful share of people
who leave give no warning in the data at all — so it should support judgement, not replace
it. This was added after an earlier version leaked the AUC into a chat reply.

It **will not pretend the low scores are safe**. Under every assessment, permanently: about
a third of customers who close look identical to customers who stay.

It does otherwise behave like a normal assistant — ask it what 2+2 is and it answers 4,
rather than demanding customer details.

---

## 6. End to end

1. A marketing employee opens the chat window (`streamlit run agent/chat.py`).
2. The opening screen states what the tool does, that it needs 25 details, and offers three
   clickable examples — nobody has to guess what to type.
3. They type or paste what they know about the customer, in ordinary English.
4. Python extracts what it can — numbers, yes/no words, six-month lists — and the language
   model handles the rest.
5. A progress bar shows *18 of 25 details collected*, with an expander listing exactly what
   is still missing. Visible, so it is clear the tool is not quietly filling in blanks.
6. Anything out of range comes back as a plain sentence: *"salary is 900, outside the 2,000
   to 70,000 range seen in the data. Typo?"* Never a stack trace.
7. Once all 25 are in, the tool runs: the pipeline builds the features, clips, scales and
   scores.
8. The screen draws four blocks — **risk** (a number, a bar, and the acting line marked on
   the bar itself), **why** (the reasons, which are exact because they are
   `scaled value × coefficient`), **worth to the bank** and **expected gain** side by side,
   and **the offer** in a dark card because that is the thing to act on.
9. The employee can keep talking — ask why, ask what if, ask for a re-assessment.

---

## 7. Tech stack

**Modelling** — Python, pandas, numpy, scikit-learn 1.6.1, matplotlib. Phases 1 to 3 ran in
Google Colab; the notebook is `notebooks/churn_analysis.ipynb`, 115 cells, structured so
every step is an explanation cell, then code, then a "what we gained" cell.

**Model artifact** — `models/churn_model.pkl`, 821 KB, saved with joblib. The whole
pipeline, not just the classifier.

**scikit-learn is pinned to 1.6.1** in `requirements.txt`. The pickle was built with that
version; loading it under another produces an `InconsistentVersionWarning` and, in the
worst case, different numbers with nothing to warn you.

**Agent** — Ollama running **qwen3:4b** locally, with `think=False` and `/no_think` so it
does not narrate its reasoning at the user. Local tool calling.

**Interface** — Streamlit, with `session_state` for the conversation and custom CSS for the
cards. Navy-to-teal header band, tinted blue-grey page so the white cards lift off it, and
colour used only to carry meaning — teal for what the customer is worth, amber for expected
gain, navy for the offer, red/amber/green for risk. The reasoning is written up in
`docs/UI_DESIGN_NOTES.md` with sources.

**Development** — VS Code with a virtual environment, run configurations in `.vscode/`.

---

## 8. What was shown, and what came back

The manager reviewed the work in progress several times. What is recorded:

**On the code.** Too complicated, and disappointed that it looked like AI had written it.
This drove a real rewrite: **1,425 lines down to 541, seven files down to four, and every
class removed** from the agent layer. A 15-page PDF study guide, `docs/Agent_Code_Guide.pdf`,
was written to walk through how each line works. (The agent files have grown again since,
to 1,569 lines, as validation, routing and the interface were added.)

**On the presentation.** The first version spent too long on feature engineering. Rebuilt
to spend more time on the model phase and on what was tried and failed. The result is
`docs/Churn_Journey_Deck.pptx`, 31 slides, checked slide by slide against rendered images
for overlaps.

**On the interface.** Did not like it. That triggered a research pass on chatbot UI and UX,
a rebuild around four principles — capability transparency, persistent context, confidence
display, recovery — and then a second pass because the all-white version read like a
hospital form.

**On the model.** Asked for preprocessing to be added to the agent. The answer was that all
four preprocessing steps are already inside the saved pipeline; this was **verified by
byte-scanning the pickle** rather than asserted. Input validation was added on the agent
side, which is a different thing and was the real gap.

**On the offers.** Set the two tasks that became the whole decision layer: whether a
predicted churner is worth an offer at all, and gathering real retention offers a bank
actually makes.

**The final internship demo and its outcome are NOT RECORDED.** The internship is still in
progress and Phase 5 has not started.

---

## 9. What this does not do

**It predicts who will leave, not who can be saved.** These are different questions. The
right technique for the second is uplift modelling, which needs a control group — some
at-risk customers who deliberately get no offer — and that experiment has never been run.
**This is the honest headline limitation of the project.**

**The money figures are placeholders.** The four rates and the offer costs are invented
stand-ins, marked as such in the code. Every EGP figure the agent prints is directionally
useful and numerically provisional until the bank supplies the real ones.

**About a third of churners are invisible.** Proven, not suspected — see the ceiling test.
Their reason for leaving is not in the 29 columns.

**Offer success rates are guesses.** 40% for distressed and 25% for drifting are assumptions
with nothing behind them. They drive the break-even rule directly, so they matter a lot.

**One dataset, one point in time.** No seasonality, no drift monitoring, no retraining
schedule. If customer behaviour shifts, nothing here notices.

**The threshold is tuned for F1, not for money.** F1 treats a missed churner and a false
alarm as equally bad. They are not. The right threshold needs the real cost of an offer.

**Not deployed and not load-tested.** It runs on one machine, one conversation at a time.

**Loose ends in the notebook.** Three cells still contain "fill in from the output above"
placeholders in Phase 3, two feature switches sit at their defaults, and the slide deck
carries a few pre-rewrite numbers.

**Phase 5 — proper testing and the final write-up — has not started.**

---

## 10. What comes next

1. **Get the eight real numbers from the bank.** Nothing about the money side is
   trustworthy until then, and it is the cheapest thing on this list.
2. **Run a proper holdout.** A slice of at-risk customers who deliberately get no offer.
   Without it, nobody can say whether any of the offers work.
3. **Then build the uplift model** on what that experiment produces. That is the model this
   project actually wants and cannot yet train.
4. **Finish Phase 5** — test the agent properly and write it up.
5. **Close the notebook loose ends** and refresh the deck numbers.
6. **Decide on monitoring** — how anyone would find out that the model has gone stale.

---

## 11. What is in this package

```
churn-prevention-agent/
├── PROJECT_SUMMARY.md          this file
├── MEMORY.md                   decisions log, carried across sessions
├── requirements.txt            generated by scanning every import
│
├── agent/                      the Phase 4 agent
│   ├── agent.py                conversation, extraction, routing
│   ├── tool.py                 scoring, value, churner type, assessment
│   ├── offers.py               8 offers + NO_OFFER, plain if/else
│   ├── churn_features.py       pipeline classes - DO NOT EDIT
│   ├── chat.py                 Streamlit window, no logic
│   ├── LEARN.md, README.md, SETUP_PHASE4.md
│   └── archive_steps/          the build, one step at a time
│
├── notebooks/                  Phases 1-3
│   └── churn_analysis.ipynb    the main one, 115 cells
│
├── models/churn_model.pkl      821 KB - the full pipeline
│
├── data/schema/                SCHEMA ONLY - no real client data
│   ├── schema.json             29 columns, dtypes, ranges, class balance
│   └── synthetic_sample_5rows.csv   5 invented customers
│
├── prompts/                    every prompt, extracted
│
├── evaluation/                 metrics, confusion matrix, coefficients, plots
│
├── docs/                       experiment log, offer framework, UI notes,
│                               code guide PDF, slide deck, open questions
│
└── src/                        data preparation helpers
```

**On the data:** the raw and processed CSVs were excluded and the package was verified to
contain zero CSV files other than the synthetic five-row sample.

**On the plots:** no figures were saved during the original Colab work. Everything in
`evaluation/plots/` was re-drawn from the numbers in `docs/EXPERIMENT_LOG.md`, and each is
labelled MEASURED or DERIVED. See `evaluation/plots/README.md`.

**To run it:**

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
ollama pull qwen3:4b
streamlit run agent/chat.py
```
