# Project memory — Churn Prevention Agent

Everything established so far. Read this first in any new chat on this project.

---

# 1. The person I am working with

**Abdelrahman Hamdy.** Internship project at a bank, for the marketing team. The work is submitted to his **manager**, not to the bank itself.

**Deliverables:** a presentation and a written report. Not a production system.

**Background: beginner** in machine learning and Python. This matters more than anything else in this file.

**He must be able to defend every decision out loud.** That is the whole constraint on the project. A simple system he understands completely beats an impressive one he cannot explain.

## How he wants to work

- **Step by step, one thing at a time.** He will say "I don't understand anything" if given too much at once, and he has said it. Believe him.
- **No jargon without defining it first.** He does not know terms like tenure, correlation, AUC, leakage, interaction until they are explained. Explain on first use, in plain words.
- **Short, direct answers.** Ask him a question when something is unclear rather than guessing.
- **He wants to understand, not just receive.** Teach — ask him questions, let him reason, correct him gently. This works: he has produced good ideas when given room.
- **Everything gets documented.** He has said repeatedly not to lose progress. Update the living docs after any finding or decision.
- **The notebook is HIS work. Never write his name in it, and never attribute ideas to him in third person** ("Abdelrahman's hypothesis"). Deliverables are written in a neutral voice — "an idea worth testing", "this was tested and rejected". He corrected this directly.
- **Text cells must be plain.** Short sentences, no dense stacking. He asks for simplification when they get heavy — pre-empt it.
- **THE EXPLANATION STYLE THAT WORKS (he asked for it explicitly).** No tables. Plain sentences with the numbers written out as a short list. Always restate what a number *means* before using it — e.g. "44 means: out of 100 customers like that, 44 closed their card." Then give the four or five numbers as bullet lines, then one sentence saying what the comparison shows. He said "wow I understand now, please explain like that every time." Stacked markdown tables lose him.
- **Notebook rule (his, from Phase 2): every step ends with a "What we gained" text cell** — plain language, what that step actually bought us. Written as we go, not retrofitted. The notebook doubles as the draft of the report.
- **He is organized and likes structure.** Numbered decisions, change logs, clear file names.

## Mistakes I made that he corrected — do not repeat

1. **Dumped research at him full of unexplained terms.** He said "I don't understand a thing." Explain concepts before using them.
2. **Made slides full of numbers** when he wanted the conceptual/theoretical questions.
3. **Then made them too general** when he wanted questions specific to his dataset.
4. **Ran the data analysis myself** when he asked for a project summary. He wants to do the work with me, not be handed results.
5. **Built a full notebook** when he wants to build it together, cell by cell.

**The pattern: do less, explain more, ask before assuming.**

---

# 2. The project

## What it is

A chat assistant for the bank's marketing team.

A marketing employee describes a credit card customer. A machine learning model predicts whether that customer will close their card and explains why. The agent reads those reasons and proposes a retention offer aimed at the specific reason.

**One agent, one tool.** The agent is a loop written directly against a language model API. Its only tool is `predict_churn`, a Python function wrapping the trained model, returning a prediction, a probability, and the reasons behind it.

## Critical definition

**Churn means the customer closed their credit card.** They remain a customer of the bank — they ended this one product.

This was corrected late and matters:

- The twelve monthly columns are **card** purchases and **card** payments
- `has_other_credit_cards` is direct competition for this specific product
- Every offer is a **card retention** offer, not bank retention
- The leakage worry about `salary_lands_in_bank` largely dissolves — closing a card does not stop a salary arriving

## No customer database

The marketing person types the customer's details into the chat. The agent must run a short interview: work out which fields the model needs, ask for them a few at a time, notice what is missing, and never invent a value.

---

# 3. The technology, and why

| Choice | Reason |
|---|---|
| Python | The ML libraries only exist for it; one language across both halves |
| pandas | Loading and inspecting the table |
| scikit-learn | Train/test split, baseline model, evaluation |
| XGBoost | Data is a table of mixed types and the effects are combinations, not straight lines. Trees find those |
| SHAP | Reasons behind one specific prediction. Exact, fast method exists for tree models |
| Google Gemini API | Free tier, no card, **supports function calling** — the entire mechanism the agent needs |
| **No agent framework** | The loop is ~40 lines. Owning it means every question has an answer in our own code, not "the framework does it" |
| Streamlit | Chat window in ~30 lines. The interface is not the contribution |
| Google Colab | Notebooks run there. No local setup to fight |
| GitHub (private) | Single source of truth. Colab saves straight to it |

**Free tier warning:** never type real customer data into the agent — on the free tier Google may use submitted content and human reviewers may see it. Use invented customers. The model trains locally so the dataset itself never leaves the machine.

---

# 4. The dataset

`data/raw/bank_churn_dataset.csv` — 8,500 customers, 29 original columns, no missing values, no duplicates. **1,697 (20%) closed their card.**

**Month 1 is the OLDEST month, month 6 the most recent.** Confirmed with the manager. Everything about direction depends on this.

## Columns

Personal — age, gender, married, has_dependents, employment_sector, salary
Banking — salary_lands_in_bank, loyalty_years, iscore, has_other_credit_cards
Loans — had_loan_ever, number_of_loans, is_paying_old_loan, outstanding_loan_balance, missed_loan_payment_ever
Behaviour — payment_month_1 to 6, purchase_month_1 to 6
Answer — churned

## Suspected synthetic

Unusually clean — no missing values, no duplicates, very regular. Expect the model to score above the 0.71–0.85 range published for real bank churn data. **That would be a property of the data, not skill.** Say so before being asked.

---

# 5. Findings (all from code run on the actual file)

## The main one

Any single month barely separates the groups — month 1: leavers 1,702, stayers 1,682. Across six months they pull apart — month 6: leavers 1,239, stayers 1,793.

Sorted by spending trend, closure rate runs **65 per 100 down to 2.5**. Strongest signal in the file, and it had to be built.

**Why the average fails:** a customer flat at 1,500 and one sliding 2,000→1,000 both average 1,500.

## Trend measurement

Six versions tested, scores 0.784 to 0.806 — nearly identical. **Slope of a line through all six months** chosen (uses all data, one odd month cannot distort it). Simple percentage kept for explaining to humans.

Steepness matters continuously: >30% fall = 70 per 100; 20–30% = 42; 10–20% = 28; 5–10% = 19; flat = 12; growing = 6. **Never turn it into a yes/no flag.**

**Exact definitions — pinned down in the notebook (Phase 2, Steps 4–6) so these figures stay reproducible:**

- `purchase_slope` = `np.polyfit([1..6], six monthly purchases, 1)[0]`. Group means: **stayers +22/month, leavers −93/month.**
- `purchase_pct_change` = `(mean of months 4–6 − mean of months 1–3) / mean of months 1–3`. **Halves, not month 6 vs month 1** — that distinction matters and month-6-vs-month-1 does *not* reproduce the published figures (it gives 54.5 for the >30% band instead of 70).
- **The "65 down to 2.5" figure is confirmed: it is `purchase_pct_change` cut into 10 equal-sized bands → 64.9 down to 2.5.** It is *not* the slope. Slope in 6 bands gives 48.6 → 3.9; slope in 10 bands gives 52.6 → 2.6. All three are correct — always state which measure and how many bands, or the numbers look contradictory.

## Strongest static signals

| | Closed per 100 |
|---|---|
| Missed a loan payment ever | 46 |
| Never missed one | 15 |
| Salary paid elsewhere | 29 |
| Salary paid into our bank | 13 |
| Single, no children | 29 |
| Married with children | 15.6 |
| Self-employed | 27 / Private 20 / Government 17 |
| Has card elsewhere | 24 / Doesn't 17 |

**`salary_lands_in_bank` is the most valuable because it suggests an action**, not just a description — incentivise the salary transfer.

## Predict nothing

- **Gender:** men 20, women 20. Also fails combined with family situation, declining spend, salary deposit.
- **Salary:** correlation −0.006. Closing a card is not about affordability, it is about engagement.

## iScore — the correlation trap

Correlation −0.154 looked weak. In bands: below 580 = 30 per 100; 580–650 = 23; 650–720 = 18; above 720 = 13. **A low correlation means no straight-line relationship, not no relationship. Always check bands.**

## Interactions

| | Not declining | Declining |
|---|---|---|
| Never missed a payment | 8 | 31 |
| Has missed one | 14 | **52** |

Neither factor alone explains the corner. This is why trees were chosen.

## Two kinds of churner — shapes the offer logic

| | Distressed (575) | Drifting (724) |
|---|---|---|
| Spending change | −33% | −20% |
| Age | 39 | 33 |
| Years with bank | 4.4 | 2.4 |
| Outstanding loan | 11,610 | 6,094 |
| Salary paid to us | 41% | 17% |
| Card elsewhere | 45% | 54% |

**Distressed = money problem. Drifting = relationship problem.** Same risk score, opposite correct offer. This is the strongest justification for an agent that reasons rather than a lookup table.

## The ceiling

**398 churners (23%) are statistically identical to stayers** — same age, tenure, iScore, and they miss payments *less* often. Undetectable with this data.

Of those, **84 grew spending >15% and left anyway** — the best customers in the book (iScore 688, 80% salary deposited, 5.7 years, 1.2% missed payments). Their loan balances are 38% above stayers'. **Hypothesis: they refinanced elsewhere.**

## Operational segmentation

- Salary with us + no card elsewhere + not declining: **27% of the book, 6 per 100**
- Salary elsewhere + card elsewhere + declining: **12% of the book, 43 per 100**

## Ideas tested and rejected — keep these in the report

1. **Abdelrahman's:** gender might matter for a married man with children. Rejected — married with children: women 15.7, men 15.5. **But the reasoning was right about the mechanism**, and produced the `responsibility` column (29 → 15.6 per 100).
2. **Mine:** payments falling faster than purchases signals distress. No pattern.
3. **Mine:** a steepening fall means departure is nearer. No pattern.

## Quality checks

**Leakage — none found.** Suspected `salary_lands_in_bank`. Method: assume worst case, work out what data would look like, check. 594 of 1,697 leavers (35%) still had salary landing. Also: no zeros anywhere in the monthly columns; 109 leavers had >10 years tenure.

**Overlap — one found.** `is_paying_old_loan` is exactly `outstanding_loan_balance > 0`, zero mismatches in 8,500. Removed; kept the balance because it adds the amount.

**Contradictions — none found, and the absence is itself the finding.** Five cross-column rules run in the notebook (Step 2c): never-had-a-loan vs loan count / owed balance / missed payment; zero loans vs owed balance; tenure greater than age−18. **All five return 0 across 8,500 rows.** Real banking data entered by staff over years normally contains some contradictions. Perfect consistency is a fingerprint of generated data — this strengthens the synthetic hypothesis rather than being good news. Supporting detail: 1,697/8,500 = 19.96%, three rows off a round 20% target. Confirmed alongside: 0 empty cells, 0 duplicate rows, 6,803 stayed / 1,697 closed.

---

# 6. Decisions (numbered, with reasons)

1. Build trend columns from the monthly columns — the change separates, the level does not
2. Keep all other columns — a quarter of churners are not declining
3. **Remove `gender`** — no signal, and banking regulation restricts using it in credit/offer decisions
4. **Remove `customer_id`** — a name, not a fact
5. **Remove `is_paying_old_loan`** — exact duplicate of balance > 0
6. XGBoost — mixed-type table, combination effects. **Provisional — see decision 16**
7. Split before anything else — otherwise the score is fiction
8. Handle imbalance by weighting, **not SMOTE** — synthetic rows add noise and produce nonsense for yes/no columns
9. Never judge on accuracy — "nobody closes" scores 80%
10. Trend stays a number, never a flag
11. Slope for the model, percentage for explaining
12. Do not build divergence or acceleration columns — both tested, no signal
13. State the 23% ceiling openly in the report
14. The offer catalogue must serve two customer types
15. Always inspect bands, never dismiss on correlation alone
16. **Test XGBoost and CatBoost head-to-head in Phase 3, choose on evidence.** Abdelrahman's suggestion, from a Kaggle notebook. Both are gradient-boosted trees — same idea, different engineering; benchmarks put them within a point or two and the winner is dataset-specific. CatBoost's advantage is native handling of text categories, which barely applies here (one text column, `employment_sector`, three values). Not a reason to switch on hearsay, and not a reason to dismiss it either — same split, compare, keep the winner, put the comparison in the report. Turns "I heard it's better" into "I tested both." SHAP supports both, so the explanation layer is unaffected. Colab note: XGBoost preinstalled, CatBoost needs `!pip install catboost`

## Columns built (11)

`purchase_slope`, `purchase_pct_change`, `payment_slope`, `recent_purchases`, `quiet_months`, `purchase_volatility`, `payment_ratio`, `responsibility`, `spend_to_salary`, `loan_burden`, `relationship_depth`, plus `churner_type` for the agent.

**Scored on separation strength (distance from 0.50):**

purchase_slope 0.31 · purchase_pct_change 0.30 · payment_slope 0.30 · purchase_volatility 0.17 · payment_ratio 0.17 · recent_purchases 0.13 · spend_to_salary 0.11 · relationship_depth 0.09 · responsibility 0.09 · **quiet_months 0.05** · **loan_burden 0.02**

**loan_burden and quiet_months are weak** and need a reason to stay. `purchase_volatility` is partly the trend in disguise — a falling series is mechanically more variable.

---

# 7. Files

```
Chrum Prevention Agent/          (folder name has a typo; GitHub repo should be "churn-prevention-agent")
├── MEMORY.md                    ← this file
├── .gitignore                   excludes .env, venv, data/raw, models
├── data/raw/bank_churn_dataset.csv
├── notebooks/churn_analysis.ipynb   Part 1 (analysis, Steps 1-15) + Part 2 (preprocessing) + Phase 3
├── notebooks/churn_clean_build.ipynb  ← clean rebuild on Geron's Chapter 2 structure, 23 cells
├── src/prepare.py                   the one function that turns raw data into model input
├── src/plot_monthly_trend.py        the chart function, runs
└── docs/
    ├── EXPERIMENT_LOG.md            ← EVERY experiment with numbers, incl. failures. For the report.
    ├── PROJECT_SUMMARY.md           the whole project in one document
    ├── PHASE1_ANALYSIS_AND_FEATURES.md   ← THE LIVING DOC. Every finding and decision
    ├── Project_Workflow.pdf         3-page workflow: phases, data phase, model phase
    ├── QUESTIONS_FOR_MANAGER.md     running question log
    ├── SETUP.md                     Python, Gemini key, venv, GitHub — step by step
    ├── PLAN.md                      the full implementation plan
    ├── DATA_ANALYSIS_RESEARCH.md    what the field does, traps, uplift modelling
    ├── PRESENTATION_GUIDE.md        what to say per slide
    ├── Churn_Questions_Deck_v5.pptx ← current deck (11 slides, delete v1–v4)
    └── Churn_Agent_Plan_v3.docx     ← current one-pager (delete the others)
```

**Housekeeping owed:** delete old deck versions v1–v4, old plan docx versions, and `notebooks/01_exploration*.ipynb` (locked when last tried).

---

# 8. Where we are

| Phase | Status |
|---|---|
| 1. Setup and planning | Done |
| 2. Data analysis and feature engineering | **Done** — notebook Steps 1–15, now includes `borrowing_rate` |
| 3. The model | **Done** — ceiling reached and proven |
| 4. The agent | **Done** — four files in `agent/`, runs locally on Ollama |
| 5. Testing and write-up | Not started |

## Phase 4 as built

**Ollama, not Gemini.** Manager's instruction. Model is `qwen3:4b`.

Four files in `agent/`, 541 lines total:

- `agent.py` — the conversation. Uses the language model in exactly two places: reading English into a tool call, and turning the result back into English.
- `tool.py` — all the thinking. `score`, `yearly_value`, `kind_of`, `assess`, plus `clean_customer` for input validation.
- `offers.py` — eight offers plus "no offer", and `pick_offer` which is plain if/else.
- `churn_features.py` — the two classes the saved pkl needs in order to open. **Never edit.**

`archive_steps/` holds the seven step-by-step files it was originally built from. Nothing imports them; they are the record of building it one piece at a time.

**Runs with `Ctrl+F5` in VS Code** (Run Without Debugging — the debugger makes scikit-learn take 30 seconds to load). `.vscode/launch.json` has two entries.

**Docs written for this phase:** `agent/README.md`, `agent/LEARN.md` (seven teaching sessions), `agent/test_customers.md` (four real customers), `docs/Agent_Code_Guide.pdf` (15 pages, every line annotated), `docs/OFFER_DECISION_FRAMEWORK.md`.

**→ Full record of every experiment with numbers: `docs/EXPERIMENT_LOG.md`. Read it before answering anything about what was tried.**

## The final model

**Logistic regression**, not a tree. In a pipeline: build features → clip extremes at 1st/99th percentile → standardise → one-hot the sector.

- Cross-validated **AUC 0.8069, churn-class F1 0.5509** at a threshold of about 0.255
- Kaggle competition (scored on F1): **0.53**. Leader 0.56, which is one standard deviation away — the same model on a kinder draw.

**The ceiling is proven, not argued.** Regenerating labels from the model's own predicted probabilities gives AUC 0.8074 (sd 0.0069) against an observed 0.8069. **The model has recovered the process that generated the data.** Maximum achievable here is AUC ≈ 0.807, F1 ≈ 0.55. Everything remaining is the random draw.

**Do not restart the optimisation.** Tested and failed: CatBoost, deeper trees, blending (r = 0.978), class weighting, SMOTE, splines, rank transforms, feature pruning at 8 levels, 13 new monthly features, all 190 pairwise products. Numbers for each are in the experiment log.

## The competition

- Metric is **F1**, established from the leaderboard, not the rules (scores cluster 0.40–0.56; accuracy would floor at 0.80)
- Test set holds **286 churners of 1,500 (19.1%)**, derived from an all-ones submission scoring 0.32 via `churners = 1500 × F1 / (2 − F1)`
- Best flag count ≈ **420**
- Leaderboard noise is **±0.024** — measured by simulating the competition 12 times

**Blocked on:** GitHub repo may not exist yet (SETUP.md Part 6). Colab needs "Include private repositories" ticked when authorising.

---

# 9. Open questions for the manager

1. Do I design the offers, or does the bank supply the list?
2. ~~All bank customers or card holders only?~~ **Answered: card closure.**
3. Over what period was the card closure measured?
4. How recent is the data?
5. Is it worse to miss a churner or waste an offer? Decides the threshold — not ours to invent
6. Who is the audience for the presentation?
7. Can real customer data go to a third-party AI service? Plan: invented customers unless told otherwise
8. When was each column recorded?
9. Anything the agent must never say?
10. Is the credit limit available? Without it, utilisation cannot be computed
11. Was a retention campaign running during the six months?
12. Does the bank hold loan closure records? Would test the refinancing hypothesis

---

# 10. Report material worth keeping

- **Uplift modelling** as the honest limitation: predicting who *will* leave is not predicting who *can be saved*. "Sleeping dogs" churn *because* you contacted them. Needs experimental data we do not have. Naming it shows we understand our own ceiling.
- Published bank churn work lands at AUC 0.71–0.85. **A model scoring 0.99 is a leakage bug, not a triumph.**
- The rejected hypotheses section — evidence the reported findings can be trusted.
- Gender removed on two independent grounds, one statistical and one regulatory.
17. **Logistic regression, not a tree.** LazyPredict put four linear models above gradient boosting; cross-validation confirmed it. The log-odds of churning is nearly a straight line in `purchase_slope` (curvature 0.15) — the generator was close to logistic, so a linear model fits the truth while a tree approximates it in steps.
18. **Build only the features a linear model cannot derive itself.** It can construct any weighted sum of columns it already has, so `purchase_slope` (a weighted sum of six months) and `recent_purchases` (an average) added almost nothing — coefficients 0.054 and 0.025. What it cannot construct are ratios, squares and products: `purchase_volatility` (0.361, highest in the model), the ten `slope_x_` interactions, `spend_to_salary`, `payment_ratio`. **That is the entire +0.016 that feature engineering was worth.**
19. **Clip the extreme 1% for the linear model.** Raises F1 from 0.5489 to 0.5509. Does nothing for trees, which use only order. Clipping at 5/95 was worse.
20. **No blending.** The two tuned models correlate at 0.978 — they make the same mistakes, so averaging adds nothing. Géron's rule is to prefer models that fail differently.
21. **No class weighting, and the reason is now demonstrated.** At weights 1, 2 and 4 the F1 moves 0.0015 while the best cut climbs 0.26 → 0.39 → 0.56. Weighting and the threshold are two controls on one lever.
22. **The split belongs before the analysis, not after.** The original notebook explored all of Phase 1 and split in Phase 2. Géron splits at step 2. `notebooks/churn_clean_build.ipynb` does it correctly.
23. **Stop optimising.** The generator-recovery test proves the ceiling. Further effort belongs in Phase 4.

## Phase 4 decisions

24. **Ollama running locally, not the Gemini API.** Manager's instruction, and it turned out to be a real improvement. Nothing leaves the machine, so the plan's warning about never typing real customer data into a hosted service disappears — this answers open question 7. No API key, no rate limit. Apache-2.0 licence on qwen3 means the bank could deploy it commercially. **Consequence: Phase 4 cannot run in Colab**, because Colab is on Google's servers and Ollama is on this laptop. Phases 1–3 stay in Colab; Phase 4 is local Python.
25. **`qwen3:4b`.** Chosen for tool calling reliability, which is the entire mechanism. About 2.5 GB, runs in roughly 4 GB of memory. **4 billion parameters is the floor** — below that, models start replying in prose when they should call the tool. If tool calling gets unreliable the fix is `ollama pull qwen3:8b`, not a code change.
26. **No SHAP.** The plan said SHAP because the plan assumed a tree. A logistic regression is a scorecard: every fact multiplied by a weight, then added. So the reasons are literally `scaled_value × coefficient`, sorted. **Exact rather than estimated**, and explainable in one sentence. SHAP exists to approximate reasons for models too complicated to read directly.
27. **Our code holds the customer's details, never the model.** First version asked the model to decide when to call the tool, work out what was missing, and phrase the question. It failed — stopped calling the tool and started answering like a maths exam, with `\boxed{}` LaTeX. **The fix was not a bigger model. It was giving the model less to do.** Now `known` is a plain dict in our code, it only ever grows, and `next_question` is plain Python. This is also the safety property: the model cannot lose or invent a detail because it is not the thing storing them.
28. **`think=False` on every Ollama call.** qwen3 thinks out loud by default, which leaks `<think>` blocks and maths notation into the answer. Also stripped defensively in `clean()`.
29. **The agent does its own preprocessing, separate from the model's.** Two genuine gaps found when the manager asked about this. First, the tool-call schema declares fields as strings, so the model hands over `"9000"` not `9000` — arithmetic on that either crashes or does something silly. Second, nothing caught typos. `clean_customer()` now converts text to numbers and range-checks every field against the real minimum and maximum in the 8,500 training customers. **The dividing line: if a step needs the training data it must live in the model; if it only needs the one customer it lives in the agent.**
30. **Simplified after manager feedback.** He said the code was too complicated and could have been much simpler. He was right. **1,425 lines → 541. Seven files → four. Zero classes.** Removed: the JSON rules engine, the `Interview` class, the escalation ordering, the `_field()` dispatch function, the break-even indirection, the separate Streamlit app. Offers became eight readable if-statements.

## Phase 4 findings worth keeping

- **The dataset is Egyptian.** `iscore` is I-Score, Egypt's credit bureau (published range roughly 400–850; ours is 385–850). Salaries 2,000–69,790 monthly are EGP, median 7,046. So the offer catalogue is built from what CIB and NBK actually market, not American travel-rewards cards.
- **Risk does not tell you who is worth keeping.** Inside the riskiest fifth, annual customer value runs from about 806 EGP at the 10th percentile to 6,856 at the 90th — **8.5x spread at the same risk score**. Correlation between declining spend and value is 0.19, close to nothing. The safest fifth is the *most* valuable (median 4,196 against 2,284).
- **Every customer in the file repays less than they spend.** Median repays 87 of every 100; median carried balance about 2,149 EGP a year. **Interest is the largest revenue line**, which is why cutting it is the most expensive offer available.
- **The break-even rule:** a customer must be worth more than `cost ÷ (risk × save rate)`. Shape of the answer: **cheap offers are worth making to almost everyone flagged; expensive offers to almost nobody.** A 150 EGP offer at 70% risk breaks even at 536 EGP a year and 92% of the book clears it. A 1,000 EGP offer at 50% risk breaks even at 8,000 and only 4% clear it.
- **"No offer" must be in the catalogue.** An agent that always has something to give will always give something.
- **Yeo-Johnson is not in the saved model** — checked, `lambdas_` absent, so `USE_STRAIGHTEN` stayed False. The log version was measured: best AUC anywhere (0.8084/0.8085) but worse F1 (0.5484/0.5489 against 0.5509). Both drops are inside the 0.005 noise floor. **Yeo-Johnson specifically was never run**, so saying it fails is currently an inference rather than a measurement. One cell would close that.

## Still owed

- **Three blanks in the notebook.** Phase 3 Step 2 has "fill in from the output above" in three places; `USE_PARTNERS` and `USE_STRAIGHTEN` sit at defaults. He ran it, so the numbers exist — they were never written down.
- **The deck has pre-rewrite numbers** — F1 0.5509 and "+0.016 for feature engineering", from before the rank leak was fixed and `borrowing_rate` added.
- **Eight numbers from the manager:** interchange rate, card interest, loan margin, deposit margin, and the real cost of each offer. All placeholders now, all in one place at the top of `tool.py` and in `offers.py`.
- **Has the bank a save-rate figure** from past campaigns? Would replace `CHANCE_OFFER_WORKS` with a measurement instead of a guess.

## How he works — added from Phase 4

- **He must be able to defend every line.** His manager was disappointed that he could not explain the code and that AI wrote it. This is now the binding constraint: simple beats clever, and every file needs a plain reason for existing.
- **When he says "I don't understand anything", stop explaining and give one action.** Not three. One command, one file, one thing to look at. It has happened twice and both times the fix was to shrink the message, not improve it.
- **Teaching that works:** short sessions, questions he answers out loud, then change one number and predict the result before running. Reading code teaches him little; being surprised by it teaches him a lot.
