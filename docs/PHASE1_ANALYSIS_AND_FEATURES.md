# Phase 1 — Data analysis and feature engineering

**A living document.** Everything we find, every choice we make, and the reason behind each one. We keep adding to it until the phase ends.

---

# 1. What this phase is for

You have 8,500 customers. About 1,700 of them left.

**The whole job is to find what is different about the ones who left.**

That is all data analysis is here. Every technique is just a way of doing that comparison without fooling ourselves.

It splits into two jobs:

**Data analysis** — looking at what is already in the file. Compare leavers to stayers, one column at a time, then two at a time.

**Feature engineering** — building new columns out of the ones we have, when the ones we have are hiding something. We found several cases where this matters.

---

# 2. The dataset

| | |
|---|---|
| Customers | 8,500 |
| Columns | 29 |
| Left the bank | 1,697 (20%) |
| Missing values | None |
| Duplicate rows | None |

**The columns we were given:**

Personal — age, gender, married, has dependents, employment sector, salary

Banking — salary lands in bank, loyalty years (how long they have been a customer), iscore (credit score), has other credit cards

Loans — had loan ever, number of loans, is paying old loan, outstanding loan balance, missed loan payment ever

Behaviour — payments for each of the last 6 months, purchases for each of the last 6 months

Answer — churned (1 if they left, 0 if they stayed)

**Month 1 is the oldest month. Month 6 is the most recent.** Confirmed with the manager. This matters enormously — if it were the other way round, every trend column we build would point in the wrong direction and the model would learn the opposite of the truth.

## 20% is unbalanced, and that causes one specific problem

Only 1 customer in 5 left. That means a lazy model could answer "nobody ever leaves" and be right 80% of the time while being completely useless.

So **accuracy is not a measure we can use.** We need measures that ask two different questions:

- Of the people we flagged as leaving, how many really left?
- Of the people who really left, how many did we catch?

---

# 3. What we found

## 3.1 Individual months tell us nothing

Look at month 1 spending:

| | Month 1 average |
|---|---|
| Left | 1,702 |
| Stayed | 1,682 |

Almost identical. If you only had month 1, you could not tell these people apart.

## 3.2 But the six months together tell us everything

| | Month 1 | Month 6 |
|---|---|---|
| Left | 1,702 | **1,239** |
| Stayed | 1,682 | **1,793** |

They start in the same place. The leavers slide down. The stayers creep up.

So we built a new column measuring the slide, and sorted all 8,500 customers by it:

| Spending change | Left, out of 100 |
|---|---|
| Falling about 36% | **65** |
| Falling about 22% | 38 |
| Falling about 14% | 28 |
| Falling about 8% | 20 |
| Roughly flat | 11 |
| Growing about 8% | 9 |
| Growing about 13% | 6 |
| Growing about 32% | **2.5** |

From 65 down to 2.5, in perfect order. **This is the strongest signal in the dataset, and it did not exist in the file we were given.** We had to build it.

## 3.3 Why the average would not have worked

Two customers:

| | M1 | M2 | M3 | M4 | M5 | M6 | Average |
|---|---|---|---|---|---|---|---|
| Customer A | 1500 | 1500 | 1500 | 1500 | 1500 | 1500 | **1500** |
| Customer B | 2000 | 1800 | 1600 | 1400 | 1200 | 1000 | **1500** |

Same average. Completely different customers. The average cannot tell them apart — it throws away the direction. The trend keeps it.

## 3.4 How we measure the slide barely matters

There is more than one way to measure "spending is falling". We tested six:

| How we measure it | How well it separates leavers from stayers |
|---|---|
| Slope of a line through all six months | **0.806** |
| Month 6 compared to month 1 | 0.803 |
| Last 2 months vs first 2 | 0.802 |
| Last 3 months vs first 3 | 0.797 |
| Month 6 vs the six-month average | 0.787 |
| Month 6 vs their best month | 0.784 |

**What that number means:** pick one leaver and one stayer at random. How often does this measure correctly say the leaver is the riskier one? 0.50 is a coin flip. 1.00 is always right.

**All six are nearly identical.** Two percentage points between best and worst. They are all measuring the same thing.

The slope wins narrowly, and it has one extra advantage: it uses all six months, so one strange month cannot distort it.

**Decision: use the slope for the model, but keep the simple percentage for explaining to people.** "Spending fell 33%" is instantly understandable. "Slope of −87 per month" is not. The model and the explanation do not have to use the same number.

## 3.5 How steeply it falls matters — so keep it a number

| Spending change | Left, out of 100 | Customers |
|---|---|---|
| Falling more than 30% | **70** | 680 |
| Falling 20–30% | 42 | 784 |
| Falling 10–20% | 28 | 1,226 |
| Falling 5–10% | 19 | 782 |
| Roughly flat | 12 | 1,607 |
| Growing | 6 | 3,421 |

A 30% fall is five times more dangerous than a 7% fall. If we turned this into a simple yes/no "declining" flag, we would throw that away. **The trend stays a number.**

We also checked whether the trend works differently for new versus long-standing customers. It does not — the gap is between 26 and 31 points in every group. It is reliable everywhere.

## 3.6 The finding the bank can actually act on

| | Left, out of 100 |
|---|---|
| Salary paid into our bank | **13** |
| Salary paid elsewhere | **29** |

More than double.

**This is the most useful column in the dataset — not because it predicts well, but because the bank can do something about it.** Most columns describe a customer. This one suggests an action: give people a reason to move their salary across.

With having a card at another bank added in:

| | No card elsewhere | Has card elsewhere |
|---|---|---|
| Salary paid into our bank | 10 | 16 |
| Salary paid elsewhere | 26 | **33** |

## 3.7 Two columns can mean more together than apart

| | Not declining | Declining |
|---|---|---|
| Never missed a loan payment | 8 | 31 |
| Has missed a loan payment | 14 | **52** |

Declining on its own gets you to 31. Missing a payment on its own gets you to 14. Both together gets you to 52 — far more than either suggests.

This is called an **interaction**. It is the main reason we chose a tree-based model: tree models find these combinations by themselves. A simpler model only finds them if we point at them.

## 3.8 Columns that predict nothing

| Column | Result |
|---|---|
| Gender | Men 20 per 100, women 20 per 100 |
| Salary | Essentially no relationship with leaving at all |

**Salary having no effect is a real finding, not a boring one.** It means leaving is not about whether people can afford the bank. It is about whether they are engaged with it. That belongs in the report.

## 3.9 Other signals

| | Left, out of 100 |
|---|---|
| Has missed a loan payment ever | 46 |
| Never missed one | 15 |
| Self-employed | 27 |
| Private sector | 20 |
| Government | 17 |
| Has a card elsewhere | 24 |
| Does not | 17 |
| Not married | 26 |
| Married | 17 |
| No dependents | 27 |
| Has dependents | 17 |

## 3.10 A weak correlation hid a real signal

We first measured iScore with a single number called a correlation, which came out at −0.154 — apparently weak. Then we looked at it in bands:

| iScore | Left, out of 100 | Customers |
|---|---|---|
| Below 580 | **30** | 1,245 |
| 580–650 | 23 | 2,463 |
| 650–720 | 18 | 2,719 |
| Above 720 | **13** | 2,073 |

A clean staircase, more than double from top to bottom.

**Why the correlation was misleading:** correlation only measures how well a *straight line* fits. When a relationship is real but not straight, the number comes out small and the signal looks absent.

**Rule to remember: a low correlation means no straight-line relationship — not no relationship. Always look at the bands before dismissing a column.**

## 3.11 Is any column cheating? (the leakage check)

**Leakage** means using information that only exists *after* the thing you are trying to predict has already happened. It is the most common way a project like this dies, and it is dangerous because the model looks brilliant while being worthless.

The column we suspected was `salary_lands_in_bank`. It is a strong signal — but when a customer closes their account, their salary stops landing there by definition. So it might have been recording the outcome instead of predicting it.

**How we tested it.** If the column were simply recording the fact that someone left, then nearly every leaver would show "salary does not land here."

**What we found:** of the 1,697 leavers, **594 — 35% — still had their salary landing in the bank.** Nowhere near zero. The column is measuring something real.

**The method, worth reusing on anything:** assume the worst case is true, work out what the data would look like if it were, then check whether it does.

Two supporting checks:

- **No account ever goes dead.** Not one customer has a zero in any of the twelve monthly columns. The lowest purchase anywhere is 54.88. If the six months included time after people left, we would expect zeros. There are none.
- **Long-standing customers do leave.** 109 leavers had been with the bank over ten years, the longest 27 years. So `loyalty_years` is not secretly counting down to a departure date.

**Result: no leakage found.** Still to be confirmed by the bank telling us the date each column was measured.

## 3.12 Two columns that were the same column

A different problem from leakage, and easy to confuse with it:

- **Leakage is about time.** A column knows something from after the outcome.
- **Overlap is about repetition.** Two columns saying the same thing.

We checked `is_paying_old_loan` against `outstanding_loan_balance`. All 8,500 customers:

| | Balance is 0 | Balance above 0 |
|---|---|---|
| Not paying an old loan | 6,412 | **0** |
| Paying an old loan | **0** | 2,088 |

**The two empty boxes are the answer.** Nobody is paying an old loan with a zero balance. Nobody has a balance without paying an old loan. Not one person out of 8,500.

We asked whether they might be two *different* loans. If they were, some people would land in the empty boxes — someone paying loan A while owing money on loan B. Nobody does. They are the same loan.

**So the flag tells us nothing the balance does not.** But the balance tells us one extra thing: **how much.** Owing 25,000 is a very different situation from owing 1,500, and the agent needs that to decide how large an offer to make.

**Decision: keep the balance, drop the flag.** Reversible if the explanations read badly later.

## 3.13 The gender hypothesis — tested and rejected, but useful

**The idea (Abdelrahman's):** gender looks flat overall, but a married man with children carries more household responsibility. Maybe gender matters *in combination* with family situation, even though it does nothing alone.

This is the right kind of thinking — the same interaction logic that found the missed-payment result in 3.7. So we tested it.

| Situation | Women | Men | Gap |
|---|---|---|---|
| Married with children | 15.7 | 15.5 | −0.2 |
| Married, no children | 24.1 | 23.1 | −1.0 |
| Single with children | 21.2 | 21.8 | +0.6 |
| Single, no children | 27.3 | 30.8 | +3.5 |

Once you know someone's family situation, gender adds essentially nothing. The only gap is single-with-no-children at 3.5 points, on about 800 people per group — too small and too isolated to act on. Gender also adds nothing combined with declining spending or with salary deposit.

**Hypothesis rejected. But the reasoning behind it was right**, and pointed at something real. Responsibility does anchor customers — it just is not carried by gender. So we measured it directly:

| Household responsibility | Left, out of 100 | Customers |
|---|---|---|
| Single, no children | **29** | 1,619 |
| One of the two | 22.5 | 2,237 |
| Married with children | **15.6** | 4,644 |

A clean staircase, nearly twice the risk at one end. **This column did not exist in the dataset. It exists because of the hypothesis.**

**Gender stays out for two separate reasons.** It carries no signal — and separately, using gender to decide who gets credit or financial offers is restricted under most banking regulation, so even a real gap could not be acted on.

**The general lesson:** statistics cannot invent a hypothesis, only test one. A person has to supply the idea. A good hypothesis is specific and testable — not necessarily correct. This one was wrong and still produced a useful column.

## 3.14 Two completely different kinds of leaver

The most important structural finding so far.

We split the 1,299 declining leavers by whether they had ever missed a loan payment:

| | Distressed (575) | Drifting (724) |
|---|---|---|
| Spending change | −33% | −20% |
| Age | **39** | **33** |
| Years with the bank | **4.4** | **2.4** |
| Outstanding loan | **11,610** | 6,094 |
| Salary paid into our bank | 41% | **17%** |
| Has a card elsewhere | 45% | **54%** |

These are not two shades of the same customer. They are two different people.

**The distressed customer** is 39, has been with the bank four years, owes 11,600, has missed payments, and their spending has collapsed by a third. **They have a money problem.** They are spending less because they cannot afford to spend more.

**The drifting customer** is 33, joined two years ago, has never missed a payment, gets paid into a different bank, and already holds a card with a competitor. **They have a relationship problem.** They were never really ours.

**Why this matters:** offering debt relief to the drifter is pointless — they are not struggling. Offering extra rewards to the distressed customer is close to insulting — they cannot pay the loan they already have. **Same risk score, opposite correct action.**

This is the strongest justification we have for an agent that chooses the offer rather than a lookup table.

## 3.15 A quarter of the leavers are invisible

We split leavers into those whose spending was falling (1,299) and those whose was not (398), and compared both to the people who stayed.

| | Stayed | Left, declining | Left, not declining |
|---|---|---|---|
| Age | 38.6 | 35.9 | **38.0** |
| Years with the bank | 4.6 | 3.2 | **4.4** |
| iScore | 670 | 632 | **661** |
| Salary paid into our bank | 61% | 28% | **59%** |
| Has a card elsewhere | 38% | 50% | **39%** |
| Ever missed a payment | 11% | 44% | **8%** |
| Married | 69% | 54% | **68%** |
| Has dependents | 71% | 55% | **68%** |

**Read the last column against the first.** They are the same people. Same age, same tenure, same credit score, same salary behaviour — and they miss loan payments *less* often than the customers who stayed.

**There is no signal separating them.** About 23% of leavers cannot be detected from this data by any model, because there is nothing to detect them by.

**Why this is useful rather than depressing:** it tells us in advance where the model will stop improving, and gives an honest explanation for why we did not catch everyone. Saying it ourselves is far stronger than being asked.

## 3.16 The 84 who grew and left anyway

Of those 398 invisible leavers, 84 were not just flat — their spending grew by more than 15%.

| | The 84 | Stayers |
|---|---|---|
| iScore | **688** | 670 |
| Salary paid into our bank | **80%** | 61% |
| Years with the bank | **5.7** | 4.6 |
| Ever missed a payment | **1.2%** | 10.6% |
| Outstanding loan | **9,281** | 6,701 |

Higher credit score, longer relationship, salary deposited, almost never miss a payment — the best customers in the book. And they left while spending more than ever.

We checked whether our trend measure was hiding a sudden collapse in the final month. It was not — they sit closer to their own peak than stayers do. There is no hidden decline.

**The one thing that stands out is the loan balance, 38% above stayers'. Our hypothesis: they refinanced elsewhere.** A competitor took the loan, and the relationship followed it. Testable if the bank holds loan closure records.

## 3.17 Where the risk actually sits

Putting the three strongest signals together:

| Group | Share of customers | Left, out of 100 |
|---|---|---|
| Salary with us, no card elsewhere, not declining | **27%** | 6 |
| Salary elsewhere, card elsewhere, declining | **12%** | **43** |

A quarter of the book barely leaves. An eighth carries most of the risk.

**This is an operational recommendation, not just a chart.** The retention team could ignore the first group entirely and concentrate on the second.

## 3.18 Two ideas of ours that failed

Recorded on purpose. Most analysis ideas fail, and showing only the successes is how people mislead themselves.

**Idea 1 — payments falling faster than purchases signals distress.** The thinking: someone still spending but paying back less might be in trouble. Result across five groups: 15.4%, 22.4%, 23.6%, 22.0%, 16.4%. Highest in the middle, lowest at both ends — the shape of noise, not a signal. **Rejected.**

**Idea 2 — a steepening fall means departure is closer.** The thinking: someone whose decline is accelerating may be nearer to leaving than someone falling steadily. Result: 15.2%, 21.2%, 22.8%, 21.3%, 19.3%. Same shape. **Rejected.**

Neither will be built.

## 3.19 Which of our new columns actually earn their place

Built in `notebooks/01_exploration.ipynb` and scored on how well each separates leavers from stayers. Strength is the distance from 0.50, where 0.50 means the column is useless.

| Column | Strength | Verdict |
|---|---|---|
| `purchase_slope` | **0.31** | The strongest thing we have |
| `purchase_pct_change` | 0.30 | Same signal, human-readable form |
| `payment_slope` | 0.30 | Strong |
| `purchase_volatility` | 0.17 | Good, but see the caution below |
| `payment_ratio` | 0.17 | Good |
| `recent_purchases` | 0.13 | Useful |
| `spend_to_salary` | 0.11 | Useful |
| `relationship_depth` | 0.09 | Modest |
| `responsibility` | 0.09 | Modest |
| `quiet_months` | 0.05 | Weak |
| `loan_burden` | **0.02** | Almost worthless |

**Two columns we were confident about did not survive contact with the data.** `loan_burden` — debt relative to salary — sounded obviously useful and separates almost nobody. `quiet_months` is weak too. Neither is deleted yet, since a weak column can still contribute in combination, but both need a reason to stay and currently have none.

**A caution on `purchase_volatility`.** A falling series is mechanically more variable than a flat one, so part of its 0.17 is the trend signal wearing a different hat rather than new information. Worth checking whether it adds anything once `purchase_slope` is already in the model.

---

# 4. Every decision, and why

| # | Decision | Reason |
|---|---|---|
| 1 | Build trend columns from the six monthly columns | The raw months barely separate the groups. The change between them separates them enormously — 3.1 and 3.2 |
| 2 | Keep all the other columns | A quarter of leavers are not declining, so the trend alone would miss them — 3.15 |
| 3 | Remove `gender` | Two independent reasons. It predicts nothing, even combined with family situation, declining spend or salary deposit. And using gender in decisions about credit or financial offers is restricted under banking regulation — 3.13 |
| 4 | Remove `customer_id` | It is a name, not a fact about the person. A model given it will find patterns in the numbering that mean nothing |
| 5 | Remove `is_paying_old_loan` | It is exactly `outstanding_loan_balance > 0`, with zero exceptions out of 8,500. The balance says everything the flag says, plus the amount — 3.12 |
| 6 | Use a tree-based model (XGBoost) | The data is a table of mixed types, and the effects are combinations rather than straight lines — 3.7 |
| 7 | Split into train and test **before** anything else | If any information from the test customers reaches the training step, our score becomes fiction |
| 8 | Handle the 20/80 imbalance by weighting the model, not by inventing fake customers | Inventing synthetic rows is common but adds noise and produces nonsense for yes/no columns. Weighting is simpler and honest. We can test the alternative later and report what we find |
| 9 | Never judge the model on accuracy | With 20% leavers, "nobody leaves" scores 80% — section 2 |
| 10 | Keep the trend as a number, never a yes/no flag | A 30% fall is five times more dangerous than a 7% fall. A flag throws that away — 3.5 |
| 11 | Use the line-slope version of the trend for the model, the simple percentage for explaining to people | The slope wins narrowly and uses all six months. The percentage is what a marketing person can understand — 3.4 |
| 12 | Do not build the divergence or acceleration columns | Both tested. Neither showed any signal — 3.18 |
| 13 | State the model's ceiling openly in the report | 23% of leavers are indistinguishable from stayers. We cannot exceed that, and the honest explanation is worth more than the missing points — 3.15 |
| 14 | The offer catalogue must serve two customer types, not one | Distressed and drifting leavers need opposite treatment — 3.14 |
| 15 | Always inspect bands, never dismiss a column on its correlation alone | iScore looked weak at −0.154 but runs 30 down to 13 per 100 across its range — 3.10 |

---

# 5. The columns we are building

### From the twelve monthly columns

| New column | How it is built | What it captures |
|---|---|---|
| `purchase_slope` | Slope of a line through the six purchase months | Is spending sliding? **Our strongest signal** |
| `purchase_pct_change` | Last 3 months vs first 3, as a % | The same thing, in a form a human can read. For explanations |
| `payment_slope` | Same as above, on payments | Are they paying back less over time? |
| `recent_purchases` | Average of months 4 to 6 | How much they spend *now*, separate from the direction |
| `quiet_months` | How many months fell far below that customer's own normal | Catches people who go silent for a while, which an average smooths over |
| `purchase_volatility` | How much their monthly spending jumps around | Erratic behaviour the trend might miss |
| `payment_ratio` | Total payments ÷ total purchases | Are they clearing what they spend, or building up debt? |

### From the other columns

| New column | How it is built | What it captures |
|---|---|---|
| `responsibility` | `married` + `has_dependents`, giving 0, 1 or 2 | Household commitments anchor people. 29 per 100 at 0, 15.6 at 2 — 3.13 |
| `spend_to_salary` | Total 6-month purchases ÷ (salary × 6) | How much of their financial life runs through us |
| `loan_burden` | Outstanding balance ÷ salary | Debt pressure relative to earnings, rather than in raw pounds |
| `relationship_depth` | Count of ties: salary lands here, has loans, no card elsewhere | The more ties, the harder to leave |
| `churner_type` | Distressed if they have ever missed a loan payment, otherwise drifting | Two customer types needing opposite offers. Mainly for the agent — 3.14 |

### Kept exactly as they are

`age`, `loyalty_years`, `iscore`, `salary`, `married`, `has_dependents`, `employment_sector`, `salary_lands_in_bank`, `has_other_credit_cards`, `had_loan_ever`, `number_of_loans`, `outstanding_loan_balance`, `missed_loan_payment_ever`

### Removed

| Column | Why |
|---|---|
| `customer_id` | An identifier, not a fact |
| `gender` | No signal, and a regulatory problem |
| `is_paying_old_loan` | Exact duplicate of `outstanding_loan_balance > 0` |

### Still to decide

Do we keep the twelve raw monthly columns after building the trends, or drop them? Keeping them may add noise; dropping them may lose something. **We test both and keep whichever works better** — and we write down the answer rather than guessing.

---

# 6. Where we are

**Done**

- [x] Checked structure: rows, columns, types, missing values, duplicates
- [x] Checked how lopsided the answer column is
- [x] Compared leavers and stayers on every existing column
- [x] Looked at pairs of columns for interactions
- [x] Leakage check — nothing found
- [x] Overlap check — one duplicate column found and removed
- [x] Tested six different ways of measuring the trend
- [x] Tested and rejected three hypotheses
- [x] Profiled the leavers we cannot detect

**Still to do**

- [ ] Build the columns listed in section 5, in code
- [ ] Re-check each new column against leaving, to confirm it earns its place
- [ ] Check the new columns are not just copies of each other
- [ ] Decide the raw-monthly-columns question by testing
- [ ] Write the findings up with charts

---

# 7. Open questions

**For the manager**

1. ~~Is month 1 the oldest or the most recent?~~ **Answered: month 1 is oldest.**
2. **When was each column measured** — during the six months, or after the customer left? Especially `salary_lands_in_bank`. We have tested it ourselves and found no problem, but only the bank can confirm.
3. What does "churned" mean exactly, and over what period after the six months?
4. Is this real data or generated? It is unusually clean, which changes what we can claim.
5. Can the credit limit be added? Without it we cannot measure how close people are to their limit.
6. Was any retention campaign running during these six months? If some customers were already being contacted, the data is affected.
7. **Does the bank hold loan closure records?** If the 84 rising leavers refinanced elsewhere, that is testable — 3.16.
8. Is it worse to miss a leaver, or to waste an offer on someone who was staying? This decides how we tune the model.

**For us**

- Are there interactions we have not tested? We have checked declining against missed payments, salary deposit and cards elsewhere. Other pairs remain.
- What extra data would the bank need to collect to catch the invisible 23%? Complaint records, app activity, branch visits and competitor offers are the obvious candidates. Worth proposing as future work.

---

# Change log

| Date | What changed |
|---|---|
| 3 Aug | Created. First analysis: the trend finding, the salary deposit finding, interactions, columns with no signal. Decisions 1 to 8. |
| 3 Aug | Manager confirmed month 1 is the oldest month. Leakage check completed — `salary_lands_in_bank` tested and cleared. |
| 3 Aug | Overlap check on the loan columns. `is_paying_old_loan` found to be an exact duplicate and removed. |
| 3 Aug | Profiled the 398 undetectable leavers — the model's ceiling. Tested two hypotheses, both rejected. Established that trend steepness matters continuously. |
| 3 Aug | Tested the gender-and-responsibility hypothesis. Rejected, but produced the new `responsibility` column. |
| 3 Aug | Found two distinct leaver types, distressed and drifting. Profiled the 84 rising leavers with a refinancing hypothesis. Found iScore's real signal hidden behind a weak correlation. Built an operational segmentation. |
| 3 Aug | Tested six ways of measuring the trend. All within two points of each other; slope chosen for the model, percentage kept for explanation. Decision 11. |
| 3 Aug | Full rewrite in simpler language. Nothing removed. |
| 4 Aug | Built `notebooks/01_exploration.ipynb` — every check and decision above, now in runnable code. All eleven new columns built and scored (3.19). `loan_burden` and `quiet_months` turned out weak. Dataset now 38 columns after 3 removals and 11 additions. Processed file saved to `data/processed/features.csv`. |
