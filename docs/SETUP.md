# Setup guide

Do this once, before writing any project code. Every step says what you are doing and why, not just what to type.

You are on Windows, so all commands below are for **PowerShell**. Open it by pressing the Windows key, typing `powershell`, and hitting Enter.

Your project folder is:

```
C:\Users\abdel\OneDrive\Documents\Claude\Projects\Chrum Prevention Agent
```

---

# Part 1 — Install Python

Python is the language everything is written in. The machine learning libraries only exist for Python, so this is not a choice.

**Step 1.1** — Check whether you already have it. In PowerShell, type:

```powershell
python --version
```

**Step 1.2** — Read the answer.

- If it says `Python 3.10`, `3.11`, `3.12` or `3.13` — you are done with Part 1, skip to Part 2.
- If it says `Python 3.9` or lower, or gives an error, continue to Step 1.3.

**Step 1.3** — Go to <https://www.python.org/downloads/> and download the latest Windows installer.

**Step 1.4** — Run the installer. On the very first screen there is a checkbox at the bottom that says **"Add python.exe to PATH"**. Tick it. This is the step everyone skips and then spends an hour debugging — without it, PowerShell cannot find Python.

**Step 1.5** — Click Install Now and wait.

**Step 1.6** — Close PowerShell completely, open a new one, and run `python --version` again. It should now show the version you installed. If it still errors, the PATH checkbox was missed — re-run the installer and choose Modify.

---

# Part 2 — Get a free API key

## What an API key is, and why you need one

Your agent is a Python program. When it needs to think — decide what to ask the user, read the model's output, choose an offer — it sends a message over the internet to a large language model and gets a reply back. The API key is the password that identifies you when doing that.

This is separate from your Claude subscription. A subscription lets *you* chat in an app; an API key lets *your code* talk to a model.

## Which provider

You asked for free, and there is a genuinely free option that is good enough for this project: **Google Gemini**, via Google AI Studio.

Free tier gives roughly **1,500 requests per day** on the Flash models, needs **no credit card**, and does not expire. Critically for us, it supports **function calling** — the ability for the model to say "call this tool with these arguments" — which is the entire mechanism our agent depends on. Without function calling a provider is useless to us no matter how cheap it is.

Alternatives if you hit limits: **Groq** (very fast, 30 requests/minute free, also supports tool calling) and **OpenRouter** (many models behind one key). Both are worth knowing about; start with Gemini.

**One consequence to be aware of:** the agent code will use Google's Python library rather than Anthropic's. The logic is identical — send messages, receive a tool call, run the tool, send the result back — only the function names differ. If you later get budget for a paid key, swapping providers is a small change confined to one file.

## Steps

**Step 2.1** — Go to <https://aistudio.google.com/apikey>

**Step 2.2** — Sign in with a Google account.

**Step 2.3** — Click **Create API key**.

**Step 2.4** — Copy the key. It is a long string of letters and numbers.

**Step 2.5** — Paste it somewhere temporary for a moment. In Part 5 you will put it in a file properly.

**Never** paste this key into a chat, a screenshot, a slide, or a GitHub commit. Anyone who has it can spend your quota. If it leaks, delete it in AI Studio and make a new one — that takes ten seconds and costs nothing.

---

# Part 3 — Create a virtual environment

## What this is and why

A virtual environment is a private folder of Python libraries that belongs to this project alone. Without one, every project on your computer shares the same libraries, and installing something for this project can silently break another. It also means you can hand someone a list of exactly what this project needs.

**Step 3.1** — Move into the project folder:

```powershell
cd "C:\Users\abdel\OneDrive\Documents\Claude\Projects\Chrum Prevention Agent"
```

The quotes matter because the path has spaces in it.

**Step 3.2** — Create the environment:

```powershell
python -m venv venv
```

This makes a folder called `venv`. It takes a few seconds and prints nothing when it works.

**Step 3.3** — Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

**Step 3.4** — Check it worked. Your prompt line should now start with `(venv)`. That prefix means Python commands are now using this project's private libraries.

**If Step 3.3 gives a red error about "running scripts is disabled"**, Windows is blocking scripts by default. Fix it once with:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Answer `Y`, then run Step 3.3 again.

**Remember:** you must run Step 3.3 every time you open a new PowerShell window to work on this project. If you ever get "module not found" errors for libraries you know you installed, the cause is almost always a forgotten activation.

---

# Part 4 — Install the libraries

**Step 4.1** — Make sure you see `(venv)` at the start of your prompt. If not, go back to Step 3.3.

**Step 4.2** — Install everything:

```powershell
pip install pandas scikit-learn xgboost shap google-genai streamlit joblib pytest python-dotenv
```

This downloads a few hundred megabytes and takes a couple of minutes.

**What each one is for:**

| Library | What it does |
|---|---|
| `pandas` | Loads the dataset and lets you filter, clean and inspect it as a table |
| `scikit-learn` | Splitting data into train and test sets, evaluation metrics, and the simple baseline model |
| `xgboost` | The real prediction model — gradient boosting, the strongest family for tabular data like this |
| `shap` | Explains a single prediction: how much each field pushed this specific customer toward leaving |
| `google-genai` | Talks to the Gemini model, including function calling |
| `streamlit` | Turns a Python file into a chat window in your browser |
| `joblib` | Saves the trained model to a file so you do not retrain every run |
| `pytest` | Runs the tests |
| `python-dotenv` | Reads your API key from a file instead of hardcoding it |

**Step 4.3** — Record exactly what got installed:

```powershell
pip freeze > requirements.txt
```

This writes a file listing every library and its version. If your laptop dies, someone can recreate your environment from it — and it is a normal thing to include in the project write-up.

---

# Part 5 — Store the API key safely

**Step 5.1** — In the project folder, create a new file named exactly `.env` — with the dot at the front and no extension.

**Step 5.2** — Put one line in it:

```
GEMINI_API_KEY=paste_your_key_here
```

Replace `paste_your_key_here` with the key from Step 2.4. No quotes, no spaces around the `=`.

**Step 5.3** — Save and close it.

Your code will read the key from this file, so the key itself never appears in any Python file you write or share. In Part 6 you will make sure this file never reaches GitHub.

---

# Part 6 — Set up GitHub

## Why bother

Two reasons that matter for a three-week project. First, if your laptop dies on 15 August, your project still exists. Second, the commit history is evidence of how you worked — a manager can see steady progress rather than one giant upload the night before.

**Step 6.1** — Install Git from <https://git-scm.com/download/win>. Accept all the defaults in the installer.

**Step 6.2** — Close and reopen PowerShell, then check:

```powershell
git --version
```

**Step 6.3** — Tell Git who you are. This is stamped on every commit:

```powershell
git config --global user.name "Abdelrahman Hamdy"
git config --global user.email "boodihamdy2003@gmail.com"
```

**Step 6.4** — Create an account at <https://github.com> if you do not have one.

**Step 6.5** — On GitHub, click the **+** in the top right, then **New repository**.

**Step 6.6** — Name it `churn-prevention-agent`. Note the correct spelling — your local folder says "Chrum", which is a typo. It does not break anything, but the repository name is the one people see, so get it right here.

**Step 6.7** — Set it to **Private**. It is bank-adjacent work; there is no reason for it to be public.

**Step 6.8** — Do **not** tick "Add a README" or any of the other initialise options. You already have files locally and those options cause a conflict that is annoying to untangle.

**Step 6.9** — Click Create repository. Leave that page open — it shows you the commands for the next step.

**Step 6.10** — Back in PowerShell, in the project folder, start tracking:

```powershell
git init
git add .
git commit -m "chore: project setup"
```

**Step 6.11** — Connect it to GitHub and upload. Replace `YOUR-USERNAME` with your actual GitHub username:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/churn-prevention-agent.git
git push -u origin main
```

**Step 6.12** — A browser window will open asking you to sign in to GitHub. Do that once and it is remembered.

**Step 6.13** — Refresh the GitHub page. Your files should be there.

**Step 6.14** — Check the important thing: **`.env` must not be listed on GitHub, and neither should `venv` or `data/raw`.** The `.gitignore` file in the project prevents them from being uploaded. If you see `.env` on GitHub, stop, delete the repository, delete that API key in AI Studio, generate a new one, and try again.

## Saving your work from now on

After each meaningful piece of work:

```powershell
git add .
git commit -m "feat: short description of what changed"
git push
```

Commit when something works, not at the end of the day. Small commits with clear messages are what makes the history readable.

---

# Checklist

Work through these and tick them off. Do not start coding until all seven are done.

- [ ] `python --version` shows 3.10 or higher
- [ ] Gemini API key created at aistudio.google.com
- [ ] `venv` folder exists and activates, showing `(venv)` in the prompt
- [ ] All libraries installed and `requirements.txt` written
- [ ] `.env` file contains the key
- [ ] Git installed and configured with your name and email
- [ ] Private GitHub repo created, pushed, and `.env` is **not** visible on it
