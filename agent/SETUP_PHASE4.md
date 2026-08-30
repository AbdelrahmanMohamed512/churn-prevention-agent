# Phase 4 setup — the agent, on your own computer

Phases 1 to 3 ran in Colab. **Phase 4 cannot.** Ollama runs the language model on
your laptop, and Colab runs on Google's servers somewhere else — those two cannot
reach each other.

So from here we work in PowerShell, in your project folder.

Everything below is done **once**. After that, each step is just running one file.

---

## Where things live

```
Chrum Prevention Agent\
├── agent\                    ← Phase 4 lives here. New folder.
│   ├── SETUP_PHASE4.md       ← this file
│   ├── requirements.txt      ← the list of packages to install
│   └── step1_hello_ollama.py ← Step 1
├── models\
│   └── churn_model.pkl       ← MISSING. The notebook makes it. Step 2 needs it.
├── notebooks\                ← Phases 1-3. Stays in Colab.
├── data\raw\                 ← the bank file. Never leaves this machine.
└── docs\                     ← the report, the deck, the experiment log
```

Nothing else moves. The agent folder sits alongside what already exists.

---

## Part 1 — Open PowerShell in the project folder

**1.1** Press the Windows key, type `powershell`, press Enter.

**1.2** Move into the project folder. The quotes matter, because the path has
spaces in it:

```powershell
cd "C:\Users\abdel\OneDrive\Documents\Claude\Projects\Chrum Prevention Agent"
```

**1.3** Check you are in the right place:

```powershell
dir
```

You should see `agent`, `data`, `docs`, `models`, `notebooks`, `src`, `tests`.

---

## Part 2 — Make a virtual environment

### What this is, and why

A virtual environment is a private copy of Python that belongs to this project
only. Packages installed inside it cannot break anything else on your computer,
and anything else on your computer cannot break this project.

It is one command, and it is the difference between "it worked last month" and
"it still works".

**2.1** Create it:

```powershell
python -m venv venv
```

This makes a `venv` folder. It is already excluded from Git — it is not part of
the project, it is a tool.

**2.2** Turn it on:

```powershell
.\venv\Scripts\Activate.ps1
```

Your prompt line should now start with `(venv)`. **That is how you know it is on.**

**If you get a red error about "running scripts is disabled"**, Windows is
blocking it by default. Run this once, then repeat 2.2:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**2.3** Remember: every new PowerShell window starts with it OFF. If a command
fails with "module not found", the usual cause is that you forgot 2.2. Just run
it again.

---

## Part 3 — Install what Phase 4 needs

With `(venv)` showing:

```powershell
pip install -r agent\requirements.txt
```

This takes a couple of minutes. It installs six things: `ollama` to talk to the
language model, `scikit-learn`, `pandas`, `numpy` and `joblib` to load and run
the churn model, and `streamlit` for the chat window in Step 7.

---

## Part 4 — Check Ollama is ready

**4.1** In the same window:

```powershell
ollama list
```

You should see `qwen3:4b` in the list. If nothing appears, run
`ollama pull qwen3:4b` and wait for it.

**4.2** If `ollama list` errors instead, Ollama is not running. Open a **second**
PowerShell window and run:

```powershell
ollama serve
```

Leave that window open — it is the model waiting to be asked something. Go back
to the first window to carry on.

---

## Part 5 — Run Step 1

```powershell
python agent\step1_hello_ollama.py
```

It checks Ollama is reachable, checks the model is installed, sends one sentence,
and prints the reply.

**That is the whole setup.** Every step after this is `python agent\stepN_....py`.

---

## The one thing still missing

`models\churn_model.pkl` does not exist yet. Step 2's tool loads it.

To produce it: run the notebook through Phase 3 in Colab, and the last cell saves
and downloads `churn_model.pkl`. Put that file in the `models\` folder here.

**A warning worth having in advance.** The file is created by Colab's version of
scikit-learn and opened by yours. If the versions differ you may see a warning
when loading it, or in the worst case an error. If that happens, tell me the
message — the fix is to pin the version, not to retrain anything.
