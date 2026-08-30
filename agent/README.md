# The agent

A chat assistant for the marketing team.

**A marketing employee describes a customer in ordinary words. The assistant works
out whether they are about to close their credit card, why, whether they are worth
keeping, and which offer to make.**

Four files. 541 lines. No framework.

---

# Running it

**1. Ollama must be running.** On Windows it starts by itself — look for the icon in
the system tray, bottom right. **Do not type `ollama serve`**; it is already running,
and that command fails with "Only one usage of each socket address". That message
means everything is fine.

**2. VS Code must use this project's Python.** Press `Ctrl+Shift+P`, type
`Python: Select Interpreter`, pick the one with **`venv`** in the path. Do this once.
If you skip it you get "No module named 'ollama'", which always means the wrong
Python, never a missing package.

**3. Press `Ctrl+F5`** — Run Without Debugging. Pick **"THE AGENT — talk to it"**.

Use `Ctrl+F5`, not `F5`. The debugger watches every line as scikit-learn loads, which
takes thirty seconds instead of two.

Or from the terminal:

```
python agent\agent.py
```

---

# The four files

## agent.py — the conversation

You type. It collects. When it has all 25 details it runs the tool and explains the
answer.

The language model is used in exactly **two** places: reading your English into a
form, and turning the result back into English. Nothing else.

## tool.py — the thinking

Four functions:

- `score()` — will they close the card, and why
- `yearly_value()` — what are they worth to the bank per year
- `kind_of()` — a money problem or a boredom problem
- `assess()` — all of the above, plus the offer, plus whether it pays

Also `clean_customer()`, which turns the model's text into numbers and catches typos
before they reach the model.

**Every number in the whole project comes from this file.**

## offers.py — the offers

Eight offers plus "no offer", and one function that picks one. Read `pick_offer` top
to bottom: the first rule that matches wins.

## churn_features.py — plumbing

The code the saved model file needs in order to open. **Never edit it.** Change one
line and the model still runs but gives different numbers, with nothing to warn you.

---

# Which way things point

```
agent.py          you talk to this
   |
   v
tool.py           does all the thinking
   |
   +---- offers.py             picks the offer
   +---- churn_features.py     lets the model file open
   +---- models/churn_model.pkl
```

Nothing points backwards. `tool.py` has never heard of `agent.py`, which is why you
can test the tool on its own with `python agent\tool.py`.

**One sentence:** agent.py talks, tool.py thinks, offers.py chooses, churn_features.py
is plumbing.

---

# Where to look when something is wrong

- wrong offer → `offers.py`, the rules in `pick_offer`
- wrong risk → `tool.py`, the `score` function
- wrong value → `tool.py`, the `yearly_value` function
- agent confused → `agent.py`, `read_details` or `next_question`
- model will not load → `churn_features.py` and `models\churn_model.pkl` must both exist

---

# Learning it

**`LEARN.md`** — seven short sessions, ten to fifteen minutes each. Read a chunk,
answer three questions out loud, then change one thing and guess what happens before
running it. Do one session, stop, do the next tomorrow.

**`..\docs\Agent_Code_Guide.pdf`** — every line of all four files with notes beside
the parts that are not obvious. The PDF is the reference; `LEARN.md` is the exercises.

**`test_customers.md`** — four real customers from the bank file, so you already know
what happened to each one. Includes one the model gets wrong on purpose.

---

# The two things to say out loud

**On what the AI decides:**

> Nothing that matters. It reads English and writes English. Every number — the risk,
> the value, the offer — comes from my own code. If the model invented a number it
> would not reach the answer, because it never produces one.

**On preprocessing:**

> The model's four preprocessing steps are saved inside the pkl file and run every
> time, using the averages learned from the 8,500 training customers. The agent does
> its own preprocessing first: text into numbers, and range checks against the real
> minimum and maximum in the data. Run `check_preprocessing.py` and it shows all four
> steps happening.

---

# The other files here

- `check_preprocessing.py` — proves the preprocessing runs. Run it if anyone asks.
- `requirements.txt` — what to install
- `SETUP_PHASE4.md` — how this was set up in the first place
- `archive_steps\` — the seven step-by-step files the agent was originally built from.
  Kept because they are the record of building it one piece at a time. **Nothing
  imports them.** Delete the folder whenever you like.

---

# What is not built

**There is no customer database.** Every detail is typed in by hand, which is how the
project was scoped. Connecting it to the bank's own records would remove most of the
typing and is the obvious next step.
