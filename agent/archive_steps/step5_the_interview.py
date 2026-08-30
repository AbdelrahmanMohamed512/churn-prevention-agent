"""
Phase 4 — Step 5: the interview.

WHAT THIS STEP DOES
-------------------
Step 4 worked only if the employee described the whole customer perfectly in one
message. Real people do not do that. This step makes the agent hold a real
conversation: it remembers what it has been told, asks for what is missing, and
runs the tool by itself once it has everything.

THE LESSON THAT SHAPED THIS FILE
--------------------------------
The first version of this step failed, and the failure is worth keeping in the
report.

We gave the language model three jobs at once: decide WHEN to use the tool,
work out WHAT was still missing, and phrase the QUESTION. A small model running
on a laptop cannot carry that much judgement. It stopped calling the tool
altogether and started answering as if it were sitting a maths exam.

So we took two of those three jobs away from it.

    The model does   : pull details out of messy English  (it is good at this)
                       explain a finished result in plain words  (also good)

    Our code does    : decide what is still missing
                       decide what to ask for
                       decide when to run the tool
                       hold every detail we have collected

The model is now used only where a model is genuinely needed. Everything that
must be reliable is ordinary Python we can read and test.

HOW TO RUN IT
-------------
    python agent/step5_the_interview.py

Type as if you were the marketing employee. 'new' for another customer, 'quit'
to stop.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama

from step2_churn_tool import assess_customer
from step3_tell_the_model import ASSESS_TOOL, CUSTOMER_FIELDS, MODEL


# Friendly names, so we ask for "their credit score" and not "iscore".
PLAIN_NAME = {
    "age": "their age",
    "married": "whether they are married",
    "has_dependents": "whether they have children or dependants",
    "employment_sector": "where they work — Private, Government or Self-Employed",
    "salary": "their monthly salary",
    "salary_lands_in_bank": "whether their salary is paid into our bank",
    "loyalty_years": "how many years they have been with us",
    "iscore": "their I-Score credit score",
    "has_other_credit_cards": "whether they hold a credit card at another bank",
    "had_loan_ever": "whether they have ever taken a loan from us",
    "number_of_loans": "how many loans they have taken",
    "outstanding_loan_balance": "how much they still owe on loans",
    "missed_loan_payment_ever": "whether they have ever missed a loan payment",
}
for i in range(1, 7):
    PLAIN_NAME[f"purchase_month_{i}"] = f"card spending in month {i}"
    PLAIN_NAME[f"payment_month_{i}"] = f"card repayment in month {i}"

PURCHASE_FIELDS = [f"purchase_month_{i}" for i in range(1, 7)]
PAYMENT_FIELDS = [f"payment_month_{i}" for i in range(1, 7)]


def tidy(text):
    """Strip the model's thinking-out-loud and maths-exam formatting."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"\\boxed\{(.*?)\}", r"\1", text, flags=re.S)
    text = text.replace("$$", "").replace("\\[", "").replace("\\]", "")
    return text.strip()


def talk_to_model(messages, tools=None):
    """One call to Ollama, with thinking mode turned off.

    qwen3 thinks out loud by default, which produced <think> blocks and LaTeX.
    Older versions of the library do not accept think=, so we fall back.
    """
    try:
        return ollama.chat(model=MODEL, messages=messages, tools=tools, think=False)
    except TypeError:
        return ollama.chat(model=MODEL, messages=messages, tools=tools)


class Interview:
    """One conversation about one customer."""

    def __init__(self):
        self.known = {}          # OUR memory. The model is not trusted with it.
        self.said = []           # everything the employee has typed, for context

    # -- what we still need -------------------------------------------------
    def missing(self):
        return [f for f in CUSTOMER_FIELDS if f not in self.known]

    def progress(self):
        have = len(CUSTOMER_FIELDS) - len(self.missing())
        return f"{have} of {len(CUSTOMER_FIELDS)} details collected"

    # -- STEP A: get the model to pull details out of what was typed --------
    def extract(self, employee_text):
        """The model's only job here: call the tool with whatever it can see.

        We do not ask it to decide anything. We ask it to read.
        """
        self.said.append(employee_text)

        prompt = (
            "Read the notes below about one bank customer and call assess_customer "
            "with every value you can find. Leave out anything not mentioned. "
            "Do not guess. Do not explain. Just call the tool.\n\n"
            "NOTES:\n" + "\n".join(self.said)
        )

        reply = talk_to_model(
            [{"role": "system",
              "content": "You extract customer details and call the tool. Nothing else."},
             {"role": "user", "content": prompt}],
            tools=[ASSESS_TOOL],
        )

        calls = reply["message"].get("tool_calls") or []
        for call in calls:
            given = call["function"]["arguments"]
            if isinstance(given, str):
                try:
                    given = json.loads(given)
                except json.JSONDecodeError:
                    continue
            for field in CUSTOMER_FIELDS:
                value = given.get(field)
                if value not in (None, "", "unknown", "null"):
                    self.known[field] = value

        return bool(calls)

    # -- STEP B: our code decides what to ask for ---------------------------
    def question(self):
        """Ask for at most four things, in plain words. Written by us, not the model."""
        missing = self.missing()

        # the twelve monthly figures are asked for as two lists, never one by one
        if all(f in missing for f in PURCHASE_FIELDS):
            return ("Can you give me their card spending for the last six months, "
                    "oldest first? Six numbers.")
        if all(f in missing for f in PAYMENT_FIELDS):
            return ("And their repayments for those same six months, oldest first? "
                    "Six numbers.")

        partial = [f for f in missing if f in PURCHASE_FIELDS + PAYMENT_FIELDS]
        if partial:
            return ("I am missing " + ", ".join(PLAIN_NAME[f] for f in partial[:4])
                    + ". Could you give me those?")

        ask = missing[:4]
        if len(ask) == 1:
            return f"One more thing — {PLAIN_NAME[ask[0]]}?"
        lines = "\n".join(f"  - {PLAIN_NAME[f]}" for f in ask)
        return f"I still need a few things:\n{lines}"

    # -- STEP C: run the tool, then let the model explain it ----------------
    def assess(self):
        result = assess_customer(self.known)

        summary = {
            "risk_out_of_100": round(result["prediction"]["probability"] * 100),
            "acting_line_out_of_100": round(result["prediction"]["threshold"] * 100),
            "will_close": result["prediction"]["will_close"],
            "main_reasons": [r["sentence"] for r in result["prediction"]["reasons"]["pushed_up"][:3]],
            "worth_per_year_egp": result["annual_value_egp"],
            "customer_type": result["churner_type"],
            "recommended_offer": result["recommended_offer"],
            "what_that_offer_is": result["offer_is"],
            "what_that_offer_fixes": result["offer_fixes"],
            "offer_cost_egp": result["offer_cost_egp"],
            "needs_to_be_worth_egp": result["break_even_egp"],
            "worth_retaining": result["worth_retaining"],
        }

        reply = talk_to_model([
            {"role": "system",
             "content": ("You explain a churn assessment to a marketing employee who is "
                         "not technical. Use short plain sentences. No lists longer than "
                         "three items. No jargon. No maths notation. Do not add any "
                         "numbers that are not given to you.")},
            {"role": "user",
             "content": ("Explain this assessment in about six sentences, covering:\n"
                         "1. the risk out of 100, and whether it is above the acting line\n"
                         "2. the two or three main reasons, in plain words\n"
                         "3. what the customer is worth to us in a year\n"
                         "4. which offer to make, what it actually is, and WHY it suits "
                         "this particular customer - use what_that_offer_fixes for that\n"
                         "5. if worth_retaining is false, say clearly to make no offer "
                         "and why it would lose money\n\n"
                         + json.dumps(summary, indent=2))},
        ])

        return tidy(reply["message"].get("content", "")), summary

    # -- one turn -----------------------------------------------------------
    def say(self, employee_text):
        called = self.extract(employee_text)

        if not called and not self.known:
            return ("I could not pick any details out of that. Could you tell me the "
                    "customer's age, whether they are married, where they work, and "
                    "what they earn?")

        if self.missing():
            return self.question()

        answer, summary = self.assess()
        if not answer:
            answer = (f"Risk {summary['risk_out_of_100']} out of 100. "
                      f"Worth {summary['worth_per_year_egp']} EGP a year. "
                      f"Offer: {summary['recommended_offer']}.")
        return answer


# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("  CHURN ASSISTANT")
    print("=" * 70)
    print("  Describe a customer in your own words. I will ask for what is missing.")
    print("  Type 'new' for a different customer, or 'quit' to stop.")
    print("=" * 70)
    print()

    interview = Interview()

    while True:
        try:
            text = input("You:  ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text.lower() in ("quit", "exit", "q"):
            break
        if text.lower() in ("new", "reset"):
            interview = Interview()
            print("\nAgent:  Starting fresh. Tell me about the customer.\n")
            continue

        print()
        print("Agent:", interview.say(text))
        print()
        print(f"        [{interview.progress()}]")
        print()


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# WHAT WE GAINED FROM STEP 5
# ---------------------------------------------------------------------------
# An agent a person can actually talk to, and a lesson worth putting in the report.
#
# The first attempt gave the language model three jobs: decide when to use the
# tool, work out what was missing, and phrase the question. It failed - it stopped
# calling the tool and began answering as though it were sitting an exam.
#
# The fix was not a bigger model. It was giving the model less to do.
#
# It now reads messy English into a tool call, and explains a finished result.
# Everything that has to be reliable - what is missing, what to ask, when to run
# the tool, what we know - is ordinary Python.
#
# That is also why nothing can be invented. The model never holds the customer's
# details and never produces a number.
# ---------------------------------------------------------------------------
