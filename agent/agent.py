"""
The agent. Talk to it about a customer and it tells you what to do.

    .\\venv\\Scripts\\python.exe agent\\agent.py

How it works:

    1. You type anything - a question, or a customer's details.
    2. If it is customer details, we pull them out and store them.
    3. If we have all 25 details, we run the tool and explain the answer.
    4. If it is not customer details, the agent just talks to you normally.

The language model only reads and writes English. Every number comes from tool.py.
"""

import json
import re

import ollama

from tool import assess

MODEL = "qwen3:4b"


# ---------------------------------------------------------------------------
# WHO THE AGENT IS
#
# This is the system prompt. It is sent with every message and it is the only
# place the agent's role is defined. Change this and you change its behaviour
# everywhere, which is why it lives at the top on its own.
# ---------------------------------------------------------------------------
SYSTEM = """You are the Churn Assistant, built for the credit card retention team
of an Egyptian bank. You help marketing staff decide what to do about a customer who
might close their card.

WHAT YOU DO
A prediction model, trained on thousands of the bank's own customers, estimates how
likely someone is to close their credit card and gives the reasons. You then work out
what that customer is worth to the bank each year, whether a retention offer would pay
for itself, and which offer from the approved list fits their actual reason for
leaving. Sometimes the right answer is no offer at all.

THE 25 DETAILS YOU NEED
Age, married, has children, employment sector, monthly salary, whether the salary is
paid into our bank, years with the bank, their I-Score credit score, whether they hold
a card at another bank, whether they ever took a loan, how many loans, how much they
still owe, whether they ever missed a loan payment, then six months of card spending
and six months of card repayments.

I-Score is Egypt's credit bureau score, roughly 400 to 850. It IS one of the fields you
use - never say otherwise.

EXPLAINING versus PRODUCING - this distinction matters
You may always EXPLAIN how something is worked out, even with no customer loaded:
  - Expected gain = how likely they are to leave, times the assumed chance an offer
    works, times what they are worth to the bank in a year.
  - Worth per year = a small cut of what they spend, plus interest on the balance they
    carry, plus margin on their loans, plus margin on their salary if it is held here.
  - The offer is chosen by the customer's problem: money trouble gets something that
    makes the card cheaper, disengagement gets something that makes it worth using.
You may NOT produce an actual risk score, value, or offer for a specific customer
without the tool having run. If it has not run, say so and offer to run it.

NEVER DISCLOSE
Do not mention model accuracy figures, AUC, F1, thresholds, the algorithm used, file
names, or how the model was trained. These are internal. If asked how accurate it is,
say only that it was tested on thousands of the bank's own customers and that a
meaningful share of people who leave give no warning in the data at all, so it should
support judgement rather than replace it.

YOU ARE ALSO A NORMAL ASSISTANT
If someone asks a general question - what 2 plus 2 is, what a credit score means, how
to word a message to a customer - just answer it. You are not limited to churn.

HOW TO WRITE
Short and plain. No jargon, no maths notation, no lists longer than three items.
Never invent a customer detail. Answer in the language the employee writes in.
Never show your reasoning - give the answer only.
For yes/no fields use 1 for yes and 0 for no, never words.

/no_think"""


# The 25 details the churn model needs, and how to ask for each one.
NEEDED = {
    "age": "their age",
    "married": "whether they are married",
    "has_dependents": "whether they have children",
    "employment_sector": "where they work: Private, Government or Self-Employed",
    "salary": "monthly salary",
    "salary_lands_in_bank": "whether their salary is paid to us",
    "loyalty_years": "years with the bank",
    "iscore": "their I-Score credit score",
    "has_other_credit_cards": "whether they have a card at another bank",
    "had_loan_ever": "whether they ever took a loan",
    "number_of_loans": "how many loans",
    "outstanding_loan_balance": "how much they still owe",
    "missed_loan_payment_ever": "whether they ever missed a payment",
}
for i in range(1, 7):
    NEEDED[f"purchase_month_{i}"] = f"card spending in month {i}"
for i in range(1, 7):
    NEEDED[f"payment_month_{i}"] = f"card repayment in month {i}"

SPENDING = [f"purchase_month_{i}" for i in range(1, 7)]
REPAYING = [f"payment_month_{i}" for i in range(1, 7)]


# The form we hand the language model, so it knows what to fill in.
TOOL_FORM = {
    "type": "function",
    "function": {
        "name": "assess_customer",
        "description": "Assess a credit card customer. Fill in every value you can find.",
        "parameters": {
            "type": "object",
            "properties": {name: {"type": "string", "description": ask}
                           for name, ask in NEEDED.items()},
            "required": [],
        },
    },
}


# A separate, deliberately tiny prompt for pulling fields out of text.
#
# The big SYSTEM prompt above is about holding a conversation - who you are, what
# offers you may recommend, what you must never claim. Sending it on an extraction
# call actively hurts: the model starts trying to be an assistant instead of
# filling in a form, and returns no fields at all. One job per prompt.
EXTRACTOR = "You read text and call the given function with any values you find. " \
            "You do not chat, explain, or ask questions."


def ask_model(messages, tools=None, system=None):
    """One message to the language model.

    think=False because qwen3 thinks out loud by default, which leaks its
    reasoning and maths notation into the reply.
    """
    full = [{"role": "system", "content": system or SYSTEM}] + messages
    try:
        return ollama.chat(model=MODEL, messages=full, tools=tools, think=False)
    except TypeError:
        return ollama.chat(model=MODEL, messages=full, tools=tools)


def clean(text):
    """Strip the model's thinking-out-loud and maths formatting.

    qwen3 reasons out loud before answering. Ollama usually removes the opening
    <think> tag but leaves the closing one, so looking for a matching pair finds
    nothing. Anything before a </think> is thinking, so we cut there.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)

    if "</think>" in text:
        text = text.split("</think>")[-1]

    text = re.sub(r"</?think>", "", text)
    text = re.sub(r"\\boxed\{(.*?)\}", r"\1", text)
    return text.replace("$$", "").strip()


# ---------------------------------------------------------------------------
# Reading six numbers out of a line
#
# A 4-billion-parameter model cannot reliably map "1200, 2000, 2500, 2800,
# 2300, 2600" onto six separate fields. So we do it ourselves, because it has
# to be right. This is the same principle as everywhere else in the project:
# the model reads English, our code does anything that must be reliable.
# ---------------------------------------------------------------------------
def find_numbers(text):
    """Every number in a line. Understands 12k as 12000."""
    found = []
    for raw in re.findall(r"\d[\d,\.]*\s*[kK]?", text):
        token = raw.strip()
        multiplier = 1000 if token.lower().endswith("k") else 1
        digits = token.rstrip("kK").replace(",", "").strip()
        try:
            found.append(float(digits) * multiplier)
        except ValueError:
            pass
    return found


# A run of six or more numbers separated by commas: "3393, 3167, 2665, ..."
SIX_IN_A_ROW = re.compile(r"\d[\d.]*(?:\s*,\s*\d[\d.]*){5,}")


def fill_six(text, known):
    """Find lists of six monthly figures and put them in the right place.

    The hard part is telling a list from a sentence. "Customer is 52, earns
    11954, with us 2.7 years" contains numbers too, and an earlier version of
    this function put his age and salary into card spending.

    So we do not take the first six numbers we see. We look for a RUN of six
    numbers separated by commas, then read the words just before it to decide
    whether it is spending or repayments.
    """
    filled = False

    for run in SIX_IN_A_ROW.finditer(text):
        numbers = find_numbers(run.group())[:6]
        if len(numbers) < 6:
            continue

        # The words just before the run usually say what it is. But a sentence
        # can mention both - "has missed a payment before. Card spending over six
        # months: 3393..." - so the keyword NEAREST the numbers wins, not the
        # first one found.
        lead_in = text[max(0, run.start() - 60):run.start()].lower()

        nearest_spend = max((lead_in.rfind(w) for w in ("spend", "purchas", "spent")))
        nearest_repay = max((lead_in.rfind(w) for w in ("repay", "repayment", "paid back")))

        if nearest_spend > nearest_repay:
            target = SPENDING
        elif nearest_repay > nearest_spend:
            target = REPAYING
        elif all(f not in known for f in SPENDING):
            target = SPENDING          # no label at all, and spending comes first
        elif all(f not in known for f in REPAYING):
            target = REPAYING
        else:
            continue

        if all(f not in known for f in target):
            for field, value in zip(target, numbers):
                known[field] = value
            filled = True

    return filled


# ---------------------------------------------------------------------------
# The easy fields, read by us rather than the model
#
# These are keyword questions, not judgement. The model kept missing them, and
# there is no reason to ask a language model whether the word "married" appears
# in a sentence. Same principle as the six numbers: if it must be right, our
# code does it.
# ---------------------------------------------------------------------------
def read_plain_words(text, known):
    """Pick up the obvious yes/no answers and the job sector."""
    low = " " + text.lower() + " "

    def says(*words):
        return any(w in low for w in words)

    if "married" not in known:
        if says("married", "wife", "husband"):
            known["married"] = 1
        elif says("single", "not married", "unmarried", "divorced"):
            known["married"] = 0

    if "has_dependents" not in known:
        if says("with children", "with kids", "has children", "has kids", "dependants",
                "dependents", "has a child"):
            known["has_dependents"] = 1
        elif says("no children", "no kids", "no dependants", "no dependents", "childless"):
            known["has_dependents"] = 0

    if "employment_sector" not in known:
        if says("self-employed", "self employed", "own business", "freelance"):
            known["employment_sector"] = "Self-Employed"
        elif says("government", "public sector", "civil servant"):
            known["employment_sector"] = "Government"
        elif says("private"):
            known["employment_sector"] = "Private"

    if "salary_lands_in_bank" not in known:
        if says("salary goes to another", "salary is paid elsewhere", "salary elsewhere",
                "salary goes elsewhere", "paid into another bank", "salary at another"):
            known["salary_lands_in_bank"] = 0
        elif says("salary is with us", "salary goes to us", "salary comes to us",
                  "salary is paid to us", "salary lands with us", "salary with us"):
            known["salary_lands_in_bank"] = 1

    if "has_other_credit_cards" not in known:
        if says("no card at another", "no other card", "no cards elsewhere",
                "no card elsewhere", "does not have another card"):
            known["has_other_credit_cards"] = 0
        elif says("card at another bank", "card elsewhere", "other credit card",
                  "has another card"):
            known["has_other_credit_cards"] = 1

    if "missed_loan_payment_ever" not in known:
        if says("never missed", "no missed payment", "always paid on time"):
            known["missed_loan_payment_ever"] = 0
        elif says("missed a payment", "missed payments", "has missed"):
            known["missed_loan_payment_ever"] = 1


def read_details(notes, known):
    """Ask the model to pull customer details out of what was typed."""
    reply = ask_model(
        [{"role": "user",
          "content": "Call assess_customer with every value you can find in these "
                     "notes about one bank customer. Do not guess. Notes:\n" + notes}],
        tools=[TOOL_FORM],
        system=EXTRACTOR,
    )

    for call in reply["message"].get("tool_calls") or []:
        found = call["function"]["arguments"]
        if isinstance(found, str):
            try:
                found = json.loads(found)
            except json.JSONDecodeError:
                continue
        for name in NEEDED:
            if found.get(name) not in (None, "", "unknown", "null", "N/A"):
                known[name] = found[name]


def next_question(known):
    """What to ask for next. At most four things. Written by us, not the model."""
    missing = [name for name in NEEDED if name not in known]

    if all(m in missing for m in SPENDING):
        return ("What was their card spending each month for the last 6 months? "
                "Six numbers, oldest first.")
    if all(m in missing for m in REPAYING):
        return ("And their repayments for those same 6 months? Six numbers, "
                "oldest first.")

    return "I still need: " + ", ".join(NEEDED[m] for m in missing[:4]) + "."


def just_talk(typed, known, last=None):
    """Reply normally. Used whenever the employee is not giving customer details.

    If we have already assessed someone, that result is handed over as context so
    follow-up questions - "why that offer?", "how did you get that number?" - can
    be answered from the real figures rather than invented ones.
    """
    missing = len(NEEDED) - len(known)

    context = (f"You have {len(known)} of {len(NEEDED)} customer details, "
               f"so {missing} are still missing. You have NOT run the tool yet.")

    if last:
        context = ("You have already assessed this customer. Here is exactly what "
                   "the tool returned - use these numbers, invent none:\n"
                   + json.dumps(last, indent=2, default=str)
                   + "\n\nIf they ask how a number was worked out: the expected gain "
                     "is the risk multiplied by the assumed chance an offer works "
                     "multiplied by what the customer is worth in a year. Do not "
                     "mention accuracy figures or how the model was built.")

    reply = ask_model([
        {"role": "user",
         "content": f"The employee said: {typed}\n\n{context}\n\n"
                    f"Answer them directly in two or three short sentences."}
    ])
    return clean(reply["message"]["content"])


def explain(result):
    """Let the model turn the tool's numbers into plain English."""
    reply = ask_model([
        {"role": "user",
         "content": "The tool has returned this assessment. Explain it to the "
                    "employee in about five short sentences: the risk, the main "
                    "reasons, what the customer is worth, and which offer to make "
                    "and why. Add no numbers of your own.\n\n"
                    + json.dumps(result, indent=2, default=str)}
    ])
    return clean(reply["message"]["content"])


# Words that mean "run it again", as opposed to a question about it.
RUN_IT_AGAIN = ("assess", "re-assess", "reassess", "run it", "run the tool",
                "check again", "recalculate", "what is the risk", "what's the risk",
                "score him", "score her", "score them")


def respond(typed, known, notes, last=None):
    """One turn.

    Returns (what to say, the assessment or None). The assessment is handed back
    so the chat window can draw the numbers properly. The terminal ignores it.

    The routing, in order:

      learned something new  -> ask for the rest, or assess if that completed it
      asked to run it again  -> assess
      anything else          -> just answer them

    That last line is the important one. An earlier version re-ran the assessment
    on EVERY message once all 25 details were in, so asking "how do you calculate
    the expected gain" produced another set of cards instead of an answer.
    """
    before = len(known)

    # Our own reading first, because it is reliable. The model fills the gaps.
    fill_six(typed, known)
    read_plain_words(typed, known)
    read_details(notes, known)

    learned_something = len(known) > before
    complete = len(known) == len(NEEDED)

    if learned_something and not complete:
        return next_question(known), None

    asked_for_it = any(phrase in typed.lower() for phrase in RUN_IT_AGAIN)

    if complete and (learned_something or asked_for_it):
        result = assess(known)
        if "problems" in result:
            return result["message"] + "\n- " + "\n- ".join(result["problems"]), None
        return explain(result), result

    # Nothing new, and they were not asking for an assessment. So talk to them.
    return just_talk(typed, known, last), None


def main():
    print("Churn Assistant. Ask me anything, or describe a customer.")
    print("Type 'new' to start over, 'quit' to stop.\n")

    known, notes, last = {}, "", None

    while True:
        try:
            typed = input("You:  ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOpen a terminal and run:  .\\venv\\Scripts\\python.exe agent\\agent.py")
            return

        if typed.lower() in ("quit", "exit"):
            return
        if typed.lower() == "new":
            known, notes, last = {}, "", None
            print("\nAgent: Starting fresh. Tell me about the customer.\n")
            continue
        if not typed:
            continue

        notes += "\n" + typed
        reply, result = respond(typed, known, notes, last)
        if result:
            last = result
        print("\nAgent:", reply)
        print(f"       [{len(known)} of {len(NEEDED)} details]\n")


if __name__ == "__main__":
    main()
