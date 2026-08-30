# Churn Prevention Agent — the full plan

Written to be read start to finish. Part A explains how the thing works with no code. Part B lists the five pieces. Part C is what to do this week, step by step. Part D covers the rest.

---

# PART A — How the whole thing works

## A.1 The two halves

The project is two separate things that meet at one point.

**The model half** is statistics. It learns from thousands of past customers what leaving looks like, and can then look at a new customer and say "this one is probably leaving, and here is what makes me think so." It cannot talk, cannot reason, and knows nothing about offers. It takes numbers in and puts numbers out.

**The agent half** is language. It talks to the marketing person, works out what information it still needs, asks for it, and once it has an answer from the model, decides what to do about it. It cannot predict anything on its own.

They meet at a single Python function. That is the whole interface between them.

## A.2 What "the model is a tool" actually means

This phrase does a lot of work in your project, so here is what physically happens.

Modern language models can be given a list of functions they are allowed to request. You describe each function in plain terms — its name, what it does, what arguments it needs. You send that list along with the conversation.

The model cannot run code. What it can do is *reply with a request*: instead of text, it sends back a structured message saying "I want you to call `predict_churn` with these values." Your Python program sees that request, runs the real function, and sends the result back into the conversation. The model then continues, now knowing the answer.

So the loop is:

1. You send: the conversation so far, plus the list of available tools
2. The model replies with either text, or a request to use a tool
3. If it is text, show it to the user and wait for their next message
4. If it is a tool request, run the function, add the result to the conversation, and go back to step 1

That is it. Four steps. When your manager asks how the agent uses the model, this is the answer, and you can point at the forty lines that do it.

## A.3 One full conversation, traced

Worth reading twice — this is what you will demo.

**The marketing user types:** "Can you check a customer for me?"

The agent has no customer details yet, so it replies asking for the first few fields — how long they have been a customer, how many products they hold, how many months they were inactive.

**The user gives some of them.** The agent checks what it has against the list of fields the model requires. Some are still missing, so it asks for those specifically. It does not guess and it does not fill in averages.

**Once every required field is present**, the agent stops talking and requests the tool.

**Your `predict_churn` function runs.** It loads the trained model from disk, arranges the fields in the exact order the model expects, and gets a prediction. Then it runs SHAP on that single prediction to find which fields pushed it toward "will leave." It returns something like:

```
will_leave: true
probability: 0.82
drivers:
  - transaction count fell 61% versus last year   (pushes toward leaving, strongly)
  - 4 support contacts in 12 months               (pushes toward leaving)
  - utilisation ratio 0.03                        (pushes toward leaving)
```

**The result goes back to the model**, which now writes the answer: this customer is at high risk; the main reason is not price, it is that they have effectively stopped using the card while contacting support repeatedly; a fee waiver would be pointless because they barely pay fees; what fits is service recovery plus a spend incentive.

**The user sees** the risk, the reasons in plain language, and a recommended offer with a justification.

The important property: every sentence in that answer traces back to a number the model produced. The agent is not free-associating about a customer, it is reading evidence.

## A.4 Why the offers are organised by reason

If your offers are just a list — fee waiver, points, rate cut — then the agent picks one by vibe, and you cannot defend the choice.

Instead each offer records **the churn driver it answers**. Then selection becomes a lookup with reasoning on top, and the same 82% risk produces different offers for different people depending on what is driving that risk. That contrast is your best slide.

This holds whether you write the offers or the bank hands them to you. If the bank gives you a list, your job becomes tagging each of their offers with the driver it addresses — which is arguably a more interesting contribution, because you are adding the structure that lets a machine choose between them. Either way the agent is the one deciding what fits this customer. That does not change.

---

# PART B — The five pieces

Built in this order, for reasons given.

| # | Piece | File | What it is | Needs data? |
|---|---|---|---|---|
| 1 | Offer catalogue | `src/offers.py` | The offers, each tagged with the churn driver it answers and a cost tier | No |
| 2 | The tool | `src/predict.py` | One function: customer in, prediction plus probability plus drivers out | Contract now, real model later |
| 3 | The agent | `src/agent.py` | The loop from A.2, plus the instructions that shape its behaviour | No |
| 4 | The interface | `src/app.py` | A chat window in the browser | No |
| 5 | The model | `src/train.py` | Trains on the dataset and saves the result to a file | Yes |

**Notice the model is last.** That looks wrong and it is deliberate. Four of the five pieces need no data at all, because piece 2 is written as a *contract* first — a function with the right shape that returns invented answers. Everything downstream is built against that shape. When the dataset arrives you replace what is inside the function, and if the tests still pass, nothing else had to change.

This buys you five days you would otherwise spend waiting, and it means the agent gets built carefully rather than in a panic at the end.

---

# PART C — This week, step by step

Sunday is when data arrives. Everything below happens before then.

## C.1 — Setup

Follow `docs/SETUP.md` end to end. Do not start C.2 until its seven-item checklist is fully ticked.

## C.2 — Build the offer catalogue

**Why first:** everything the agent does depends on knowing what it can offer, and this needs no data.

**Step C.2.1** — Open `docs/QUESTIONS_FOR_MANAGER.md` and confirm question 1 is on it. You are about to invent offers; you want to know soon whether they will be replaced.

**Step C.2.2** — On paper, list the ways a credit card customer becomes unprofitable or disengaged. There are roughly six: they stop using the card; they use it less than before; they carry a balance and resent the interest; they keep hitting their limit; they keep contacting support; they are valuable but only hold one product.

**Step C.2.3** — For each one, write the single most natural response a bank could make. Do not get creative — the obvious answer is the right one. Someone paying a fee for a card they never use wants the fee gone.

**Step C.2.4** — Give each offer a cost tier: low, medium, high. This matters because later you want to show the agent choosing a cheap offer when a cheap one fits, rather than always reaching for the most generous.

**Step C.2.5** — Create `src/offers.py` and write the list as Python dictionaries with these keys: `id`, `name`, `driver`, `cost_tier`, `rationale`.

**Step C.2.6** — Add a function `offers_for_driver(driver)` that returns every offer matching a driver name.

**Step C.2.7** — Create `tests/test_offers.py` with two tests: every offer has all five keys and a valid cost tier; looking up a known driver returns at least one offer.

**Step C.2.8** — Run `pytest tests/test_offers.py -v` and watch them pass.

**Step C.2.9** — Commit: `git add . && git commit -m "feat: offer catalogue" && git push`

**Done when:** the tests pass and you can explain, out loud, why each offer is attached to its driver.

## C.3 — Define what the model will need

**Why:** the agent has to know which fields to ask for. That list has to exist before the agent can be written, even though the model does not exist yet.

**Step C.3.1** — Create `models/feature_schema.json`.

**Step C.3.2** — Write in it the fields you expect the dataset to have. For credit card churn data this is usually: months as a customer, number of products held, months inactive in the last year, support contacts in the last year, credit limit, revolving balance, total transaction amount, total transaction count, change in transaction count between quarters, and average utilisation ratio.

**Step C.3.3** — For each field record three things: its name, its type (whole number or decimal), and a plain-English description. The description is not decoration — the agent reads it to know how to ask the user for that field.

**Step C.3.4** — Accept that this file is a guess and will be corrected on Sunday. That is fine and it is why it is a separate file rather than hardcoded in three places.

**Step C.3.5** — Commit.

## C.4 — Write the tool contract

**Why:** this is the seam. Get it right and the rest of the week is safe.

**Step C.4.1** — Create `src/predict.py`.

**Step C.4.2** — Write `missing_fields(customer)`: reads the schema, returns the names of required fields the customer dictionary does not have. The agent uses this to know what to ask for.

**Step C.4.3** — Write `predict_churn(customer)` returning a dictionary with exactly four keys: `will_leave` (true or false), `probability` (between 0 and 1), `drivers` (a list), and `model_version` (a string).

**Step C.4.4** — Decide the shape of one driver and write it down: `feature` (which field), `value` (what this customer's value was), `impact` (how strongly it mattered), `direction` (toward leaving, or toward staying). Every later piece depends on this shape, so fix it now.

**Step C.4.5** — For now, make the body of `predict_churn` return a fixed plausible answer. Mark it clearly with a comment saying it is a stub to be replaced in Phase 1.

**Step C.4.6** — Create `tests/test_predict.py` testing three things: missing fields are correctly reported; the returned dictionary has all four keys; each driver has all four of its keys.

**Step C.4.7** — Run the tests, watch them pass.

**Step C.4.8** — Read the tests once more and understand this: these exact tests will run again in Phase 1 against the real model, unchanged. Passing then is how you know the swap did not break anything.

**Step C.4.9** — Commit.

## C.5 — Build the agent

The biggest piece. Take it slowly.

**Step C.5.1** — Create `src/agent.py`.

**Step C.5.2** — Load the API key from `.env` using `python-dotenv`. Never type the key into this file.

**Step C.5.3** — Build the tool description from `models/feature_schema.json` rather than typing it out. Generating it from the schema means the two can never disagree with each other, which is a class of bug you avoid entirely rather than debug later.

**Step C.5.4** — Write the system prompt. This is the instructions the agent always sees. Cover six things, each in a sentence or two:

- who it is talking to (a bank marketing employee, not a customer)
- that it must collect the required fields before predicting
- that it should ask for a few fields at a time, not all ten at once, because a wall of questions is unusable
- that it must never invent a value it was not given
- that after the tool returns, it explains the drivers in plain language before recommending anything
- that it picks the offer matching the strongest driver, and says why that offer and not another

**Step C.5.5** — Write the loop from A.2. Send conversation plus tools; if the reply is a tool request, run `predict_churn`, append the result, send again; if it is text, return it.

**Step C.5.6** — Add a guard: if the loop goes round more than about five times, stop and return an error. Without this, a confused model can loop forever and burn your daily quota in minutes.

**Step C.5.7** — Test it from the command line first, before any interface. A plain `input()` loop in a terminal is enough. Debugging the agent and the interface at the same time is twice as hard as debugging them one at a time.

**Step C.5.8** — Hold a full conversation. Give it a customer, answer its questions, get an offer.

**Step C.5.9** — Now break it on purpose. Refuse to give a field. Give nonsense like a negative credit limit. Change your mind halfway. Watch what it does and write down anything that looks wrong — you are not fixing it yet, you are collecting a list.

**Step C.5.10** — Fix whatever is worst, usually by adjusting the system prompt rather than the code.

**Step C.5.11** — Commit.

## C.6 — Build the interface

**Step C.6.1** — Create `src/app.py`.

**Step C.6.2** — Use `st.chat_input` for the box at the bottom and `st.chat_message` to display each turn.

**Step C.6.3** — Keep the conversation in `st.session_state`. Streamlit re-runs your whole file on every interaction, so anything not in session state is forgotten between messages. This surprises everyone once.

**Step C.6.4** — Add an expander that shows the raw tool call and the drivers it returned. In the demo this is what makes the model visible — otherwise your audience sees a chatbot and has no evidence there is any machine learning behind it.

**Step C.6.5** — Run `streamlit run src/app.py` and hold a conversation in the browser.

**Step C.6.6** — Commit and push.

**Phase 0 is finished when** you can open the app, be interviewed about a customer, and receive a justified offer. The answer is fiction because the model is a stub. That is expected.

---

# PART D — After the data arrives

## D.1 — Build the model (3 to 8 August)

Written properly once the data is in front of us. The sequence:

1. **Look at the data before touching it.** Rows, columns, missing values, and above all the balance between leavers and stayers. Churn data is always lopsided — often 15% leavers — and that single fact shapes everything after it.
2. **Pin down the target.** What does the label mean and over what period? Question 2 in the manager doc.
3. **Split before you do anything else.** Hold back a test set and do not look at it again until the end. Every beginner accidentally lets test data influence training and reports a score that evaporates in reality.
4. **Build a stupid baseline.** Logistic regression. Now you have a number to beat, and a simple model to compare against in the report.
5. **Train XGBoost** with cross-validation.
6. **Judge it honestly.** With lopsided classes, accuracy is a lie — a model predicting "nobody leaves" scores 85% and is worthless. Use precision, recall, and PR-AUC, and choose the decision threshold deliberately rather than leaving it at the default.
7. **Add SHAP** to explain individual predictions.
8. **Map feature names to driver names**, so `Total_Trans_Ct` becomes `declining_spend`. This mapping is where the two halves of the project join.
9. **Save the model** and replace the stub inside `predict_churn`. Run the Phase 0 tests unchanged. If they pass, you are done.

## D.2 — Connect it for real (9 to 13 August)

Real drivers read differently from the stub, so the system prompt needs retuning. Handle the awkward cases: values out of range, a user who will not answer, a probability sitting right on the threshold.

## D.3 — Hardening (14 to 16 August)

Run fifteen real customers from the dataset through the agent and record what happened in a table. That table goes in the report and is worth more than any amount of description.

Watch specifically for an offer that costs more than the customer is worth. If you find one, that is your justification for adding a reviewer agent — a second agent whose only job is checking offers against budget, which is defensible precisely because the agent that invented an offer is a poor judge of it. If you do not find one, say so and keep a single agent. Either finding is a real result.

## D.4 — Write-up (17 to 18 August)

Report, slides, and two rehearsals of the demo. The centrepiece slide is two customers with the same risk score receiving different offers, because that single image contains the whole idea of the project.

---

# Open points

- Dataset not yet received; the feature schema is an expectation, not a fact
- Whether the offers are ours or the bank's is question 1 for the manager, and does not change the architecture either way
- Accuracy targets get set after seeing the data, never before
