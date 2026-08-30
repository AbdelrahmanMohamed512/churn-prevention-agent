# Learn this code

Seven short sessions. Ten to fifteen minutes each. Do one, stop, do the next
tomorrow. Do not read this all at once.

Each session has the same three parts:

1. **Read** — a specific piece of code, and what it does
2. **Answer** — questions to say out loud, with the answers below
3. **Try** — change one thing, guess what happens, then run it

The **Try** part is the one that matters. Reading code teaches you almost nothing.
Changing it and being surprised teaches you a lot.

---

# Session 0 — The map (5 minutes)

There are **four files**. That is the whole agent.

| File | Lines | What it does |
|---|---|---|
| `offers.py` | 101 | The twelve offers, and the rule for picking one |
| `tool.py` | 161 | Score a customer, value them, choose an offer |
| `agent.py` | 158 | The conversation |
| `churn_features.py` | 121 | Code the saved model needs. Never edit it. |

**How they connect.** Only one direction, never backwards:

```
   agent.py        you talk to this
      |
      v
   tool.py         does all the thinking
      |
      +---> offers.py           picks the offer
      +---> churn_features.py   lets the model file open
      +---> models/churn_model.pkl
```

**Say this out loud until it is automatic:**

> `agent.py` talks. `tool.py` thinks. `offers.py` chooses. `churn_features.py` is
> plumbing.

### Answer these

1. If the offer chosen is wrong, which file do you open?
2. If the risk score is wrong, which file do you open?
3. Which file should you never touch?

<details>
<summary>Answers</summary>

1. `offers.py`
2. `tool.py`
3. `churn_features.py` — it must stay identical to the notebook, or the model
   silently changes behaviour.
</details>

---

# Session 1 — offers.py (10 minutes)

Start here because it is the easiest file in the project and it has no magic in it.

## Read

Open `offers.py`. The top half is just **eight labelled boxes**:

```python
RATE_CUT = {
    "name": "Lower the interest on their balance for 6 months",
    "cost": 500,
    "fixes": "They are struggling with what the card costs them each month.",
}
```

That is a **dictionary**. The curly brackets hold pairs: a label, then a value.
`RATE_CUT["cost"]` gives you `500`. That is all a dictionary is — a labelled box.

Now the bottom half, `pick_offer`. Read it top to bottom. **The first rule that
matches wins, and nothing after it runs.**

```python
if yearly_value < 800:
    return NO_OFFER
```

`return` means *stop here and hand this back*. So a customer worth under 800 EGP
never reaches any of the rules below. That is deliberate.

## Answer these

1. A customer is distressed, worth 600 EGP a year, and owes 5,000. What offer do
   they get?
2. Why does the `yearly_value < 800` rule come first instead of last?
3. A drifting customer has their salary with us AND a rival card. Which of the two
   rules wins?

<details>
<summary>Answers</summary>

1. **No offer.** The first rule catches them and returns immediately. Being
   distressed never gets looked at.
2. Because if a customer is not worth the money, nothing else matters. Checking it
   first means we cannot accidentally recommend a 1,000 EGP bonus to someone worth
   600.
3. The salary rule, because it is written first. Order is the logic in this
   function.
</details>

## Try this

In `offers.py`, change the 800 to 5000:

```python
if yearly_value < 5000:
```

**Guess first:** what will your test customer (worth 2,719) now get?

Then run `python agent/tool.py` and check.

**Change it back to 800 when you are done.**

---

# Session 2 — yearly_value (10 minutes)

## Read

Open `tool.py` and find `yearly_value`. It is fifteen lines and it answers one
question: what is this customer worth to the bank in a year?

```python
purchases = [customer[f"purchase_month_{i}"] for i in range(1, 7)]
```

This collects the six monthly spending figures into one list. The `f"..."` builds
the name — when `i` is 3, `f"purchase_month_{i}"` becomes `"purchase_month_3"`.
`range(1, 7)` counts 1, 2, 3, 4, 5, 6. **It stops before 7, not at it.**

```python
spent_per_year = sum(purchases) * 2
```

We only have six months, so double it.

```python
share_paid_back = sum(payments) / sum(purchases)
unpaid = spent_per_year * (1 - share_paid_back)
```

If they spent 100 and repaid 76, `share_paid_back` is 0.76, so `1 - 0.76` is 0.24
and 24% of their spending stays on the card. **That unpaid part is what the bank
charges interest on, and it is the biggest source of money.**

Then four money lines added up: a cut of their spending, interest on the unpaid
part, margin on their loan, margin on their salary if it sits here.

## Answer these

1. Why multiply by 2?
2. A customer repays everything they spend. What is `unpaid`? What does that do to
   their value?
3. Their salary goes to another bank. What is `from_salary`?

<details>
<summary>Answers</summary>

1. The file only has six months. Doubling estimates a year.
2. Zero. Their value drops a lot, because interest is the largest line. **A
   customer who always pays in full is worth less to the bank than one who
   carries a balance.** That is uncomfortable but true.
3. Zero — the `if` never runs. This is why the salary transfer offer exists: it
   turns a zero into a real number.
</details>

## Try this

Add this line just before the `return` in `yearly_value`:

```python
    print("spent", spent_per_year, "unpaid", round(unpaid), "interest", round(from_interest))
```

Run `python agent/tool.py`. You now see the working. **Which of the four lines is
biggest?**

Delete the line afterwards.

---

# Session 3 — kind_of and the offer decision (10 minutes)

## Read

`kind_of` decides between a money problem and a boredom problem. Three tests, and
**any one of them** is enough:

```python
struggling = (share_paid_back < 0.80
              or customer["missed_loan_payment_ever"] == 1
              or customer["outstanding_loan_balance"] > 8000)
```

`or` means any one is enough. If it had been `and`, all three would have to be
true — and almost nobody would count as distressed.

Now find this in `assess`:

```python
expected_gain = risk * chance * value
worth_it = expected_gain > offer["cost"]
```

**Three numbers multiplied.** How likely they leave, times how likely an offer
works, times what they are worth. If that beats the cost, make the offer.

For your test customer: 0.49 × 0.40 × 2719 = about 533. The offer costs 500.
533 beats 500, so yes — but only just.

## Answer these

1. Change `or` to `and` in `kind_of`. Who would still count as distressed?
2. `CHANCE_OFFER_WORKS` is 0.40 for distressed. Where did that number come from?
3. Why does `make_the_offer` also check `risk >= threshold`?

<details>
<summary>Answers</summary>

1. Only customers who fail **all three** tests at once. Almost nobody. Most
   struggling customers would be misread as merely bored and offered the wrong
   thing.
2. **We made it up.** It is a guess, clearly labelled as one in the code. Measuring
   it properly needs an experiment where some at-risk customers are deliberately
   left alone. This is the honest weak point, and you should say so before anyone
   asks.
3. Because a low-risk customer might still clear the money test. We should not send
   an offer to someone who was never going to leave.
</details>

## Try this

Change `0.40` to `0.90` in `CHANCE_OFFER_WORKS` — pretend offers almost always
work.

**Guess:** does `make_the_offer` change? Does the offer itself change?

Run it. (Answer: the decision gets easier to pass, but the offer chosen is the
same — `pick_offer` never looks at that number.)

Change it back.

---

# Session 4 — score, the hard one (15 minutes)

This is the only genuinely difficult part of the project. Take your time.

## Read

```python
one_row = pd.DataFrame([customer])
risk = float(model.predict_proba(one_row)[0, 1])
```

The model was trained on a **table** of 8,500 customers, so it expects a table.
`pd.DataFrame([customer])` makes a table with one row in it.

`predict_proba` gives two numbers: the chance they stay and the chance they leave.
`[0, 1]` means row 0, column 1 — the second number, the chance they leave.

Now the reasons:

```python
prepared = model[:-1].transform(one_row)[0]
weights = model[-1].coef_[0]
effects = prepared * weights
```

**This is the whole idea, and it is worth understanding properly.**

Your model is a logistic regression. That means it works like a scorecard: every
fact about the customer gets multiplied by a weight, and all the results are added
up. A big total means high risk.

- `model[:-1]` is every step *except* the last — the parts that prepare the numbers
- `model[-1]` is the last step, the scorecard itself
- `.coef_` is the weights it learned
- `prepared * weights` multiplies each prepared fact by its weight

So `effects` is the list of contributions. **Sort it, and the biggest ones are
literally the reasons.** Not an estimate of the reasons — the actual arithmetic the
model did.

**This is why you do not need SHAP.** SHAP exists to estimate reasons for models
too complicated to read directly, like a forest of trees. A scorecard can be read
directly.

## Answer these

1. Why does the code build a table for one customer?
2. Why `[0, 1]` and not `[0, 0]`?
3. Your manager asks: "how do you know these are the real reasons and not a guess?"
   What do you say?

<details>
<summary>Answers</summary>

1. Because that is the shape the model was trained on. It expects a table, so we
   give it a table with one row.
2. Column 0 is the chance they stay, column 1 is the chance they leave. We want the
   chance they leave.
3. "The model is a scorecard — it multiplies each fact by a weight and adds them
   up. I am showing those multiplications, biggest first. It is the model's own
   arithmetic, not an approximation of it."
</details>

## Try this

Change `biggest[:3]` to `biggest[:8]` in `score`. Run it. You now see eight
reasons instead of three.

Notice the ones at the bottom barely matter. **That is why we only show three.**

Change it back.

---

# Session 5 — agent.py (15 minutes)

## Read

Look at `main()` first, at the bottom. It is a `while True` loop — repeat forever
until something breaks out of it.

Inside, four things happen every time you type:

```python
notes = notes + "\n" + typed        # 1. remember what you said
read_details(notes, known)          # 2. pull details out of it
if len(known) < len(NEEDED):        # 3. still missing something?
    print(next_question(known))     #    ask for more
else:
    print(explain(assess(known)))   # 4. otherwise, do the work
```

**Now the most important design decision in the project.**

Look at `read_details`. It sends your words to the language model and asks it to
fill in a form. Then:

```python
for name in NEEDED:
    if found.get(name) not in (None, "", "unknown"):
        known[name] = found[name]
```

Whatever the model found gets copied into `known`. **`known` is ours. It only ever
grows. The model never holds it.**

This matters because a small model forgets things. If we asked it to remember 25
numbers across five messages, it would drop some and invent others. So we do not
ask. We keep them ourselves, and the model just reads.

`next_question` is also ours — plain Python, no model involved. The model does not
decide what to ask for. We do.

## Answer these

1. Why keep `notes` as well as `known`?
2. What happens if the language model invents a salary that was never mentioned?
3. Which parts of `agent.py` use the language model, and which are plain Python?

<details>
<summary>Answers</summary>

1. Because we resend all the notes each time. If the model missed a detail on turn
   one, it gets another chance on turn two with the full context.
2. It would land in `known` and produce a wrong answer. **This is the real risk in
   the design**, and it is why the prompt says "Do not guess" and why the sidebar
   in the old chat window listed everything collected. If your manager asks about
   weaknesses, say this one.
3. The model is used in exactly two places: `read_details` (reading English) and
   `explain` (writing English). Everything else — `next_question`, the loop, the
   store — is plain Python.
</details>

## Try this

Add this line inside `main()`, just after `read_details(notes, known)`:

```python
        print("   [we now know:", list(known.keys()), "]")
```

Run the agent and feed it half a customer. **Watch the list grow.** This is the
single most useful thing you can see.

---

# Session 6 — churn_features.py (5 minutes)

## Read

Do not read the code. Read why it exists.

When the notebook saved `churn_model.pkl`, it saved the model's *numbers* but not
its *code*. The file contains a note that says, in effect: *"I am built from a
thing called ChurnFeatures."*

So anything opening that file must already have `ChurnFeatures` defined. In Colab
it was in the notebook. On your computer it lives in this file.

**That is the only reason it exists.** It is a copy, and it must stay a copy.

If you change one line in it, the model will still load and still produce numbers.
They will just be **different numbers**, with nothing to warn you. That is the
worst kind of bug.

### Answer these

1. Why can you not delete this file?
2. What happens if you change a line in it?

<details>
<summary>Answers</summary>

1. Because `churn_model.pkl` cannot be opened without it.
2. The model still runs but gives different answers, silently. There is no error to
   catch it.
</details>

---

# Session 7 — What your manager will ask

Practise saying these out loud.

**"Walk me through what happens when someone types a customer in."**

> The model reads my words and fills in a form. My code stores what it found. If
> anything is missing, my code asks for it. Once all 25 details are there, my code
> runs the trained model, works out what the customer is worth, picks an offer, and
> the language model turns that into a sentence.

**"What does the AI actually decide?"**

> Nothing that matters. It reads English and it writes English. Every number — the
> risk, the value, the offer — comes from my own code. If the model invented a
> number it would not reach the answer, because it never produces one.

**"Why not use a framework?"**

> The loop is about forty lines. A framework would hide it, and then every question
> about how it behaves would have the answer "the framework does it". This way I can
> point at the line.

**"Why not SHAP for the explanations?"**

> SHAP estimates reasons for models too complicated to read directly. Mine is a
> logistic regression — a scorecard. I can read the actual multiplications, so I do
> not need an estimate of them.

**"What is weakest about this?"**

> Three things. The chance an offer works is a guess, not a measurement — measuring
> it needs an experiment we do not have. The offer costs are placeholders until the
> bank gives me real ones. And the language model could in principle invent a
> customer detail, which is why I keep the details in my own code rather than
> letting it hold them.

**"Could this be simpler?"**

> It is now four files and 541 lines. It was 1,425. I cut the classes, the rules
> engine and the extra layers. What is left is the trained model, four money
> calculations, eight if-statements for the offers, and a loop.

---

# When you are stuck

Add a `print()` and run it. That is not a beginner's trick — it is what everyone
does. If you cannot tell what a line does, print the thing just before it and the
thing just after it.

```python
print("HERE:", the_thing)
```
