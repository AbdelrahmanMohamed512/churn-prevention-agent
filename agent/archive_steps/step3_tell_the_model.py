"""
Phase 4 — Step 3: tell the language model that our tool exists.

WHAT THIS STEP DOES
-------------------
Step 2 built a tool. The language model does not know about it.

This step hands the model a description of the tool - its name, what it does,
and what information it needs - and then checks one thing:

    when given a customer, does the model ASK to run our tool?

That is all. We do not run the tool here. We just look at whether the model
decided to.

WHY THIS IS THE WHOLE IDEA OF AN AGENT
--------------------------------------
A chatbot only produces words. An agent decides to DO something, and then uses
the result.

The mechanism is simpler than it sounds. We send the model a description of our
function. If the model thinks the function would help, it does not reply with a
sentence - it replies with "call assess_customer, and here are the values to
give it". Our code then runs the real Python function and hands the answer back.

The model never touches the model file, never does the arithmetic, and cannot
invent a risk score. It only decides WHEN to ask. That separation is the point.

HOW TO RUN IT
-------------
    python agent/step3_tell_the_model.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama

MODEL = "qwen3:4b"


# ---------------------------------------------------------------------------
# The description of our tool
#
# This is a form the model reads. Every field the churn model needs has to be
# listed, or the model will leave it out and our function will fail.
# ---------------------------------------------------------------------------
def number(description):
    return {"type": "number", "description": description}


CUSTOMER_FIELDS = {
    "age": number("the customer's age in years"),
    "married": number("1 if married, 0 if not"),
    "has_dependents": number("1 if they have children or dependants, 0 if not"),
    "employment_sector": {"type": "string",
                          "enum": ["Private", "Government", "Self-Employed"],
                          "description": "where they work"},
    "salary": number("monthly salary in EGP"),
    "salary_lands_in_bank": number("1 if their salary is paid into our bank, 0 if elsewhere"),
    "loyalty_years": number("how many years they have been with the bank"),
    "iscore": number("their I-Score credit score, between 385 and 850"),
    "has_other_credit_cards": number("1 if they hold a credit card at another bank, 0 if not"),
    "had_loan_ever": number("1 if they have ever taken a loan from us, 0 if never"),
    "number_of_loans": number("how many loans they have taken, 0 to 6"),
    "outstanding_loan_balance": number("how much they still owe on loans, in EGP, 0 if nothing"),
    "missed_loan_payment_ever": number("1 if they have ever missed a loan payment, 0 if never"),
}

# the twelve months of card activity
for i in range(1, 7):
    CUSTOMER_FIELDS[f"purchase_month_{i}"] = number(
        f"card spending in month {i} in EGP (month 1 is oldest, month 6 is most recent)")
for i in range(1, 7):
    CUSTOMER_FIELDS[f"payment_month_{i}"] = number(
        f"card repayment in month {i} in EGP (month 1 is oldest, month 6 is most recent)")


ASSESS_TOOL = {
    "type": "function",
    "function": {
        "name": "assess_customer",
        "description": (
            "Work out whether a credit card customer will close their card, why, "
            "what they are worth to the bank, and which retention offer suits them. "
            "Call this once you have every field. Never guess a value - if the "
            "employee has not given you a field, ask them for it instead."
        ),
        "parameters": {
            "type": "object",
            "properties": CUSTOMER_FIELDS,
            "required": list(CUSTOMER_FIELDS.keys()),
        },
    },
}


INSTRUCTIONS = (
    "You help the bank's marketing team decide whether a credit card customer is "
    "about to close their card. You have one tool, assess_customer. "
    "Never invent a customer detail. Never guess a risk score yourself - only the "
    "tool may produce one."
)


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------
def main():
    # A customer described the way a marketing employee would actually type it.
    described = (
        "Customer is 39, married with kids, works in the private sector, earns 9000 a month, "
        "salary goes to another bank. With us 4.4 years. I-Score 640. Has a card with another "
        "bank. Took 2 loans from us, still owes 11610, and yes he missed a payment once. "
        "His card spending over the last six months was 2400, 2250, 2100, 1850, 1700, 1600. "
        "His repayments were 1850, 1700, 1600, 1400, 1300, 1200."
    )

    print("Sending this to the model:")
    print(" ", described)
    print()
    print("Waiting for the model to decide...")
    print()

    reply = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": described},
        ],
        tools=[ASSESS_TOOL],          # <-- the one new thing in this step
    )

    calls = reply["message"].get("tool_calls")

    if not calls:
        print("The model did NOT ask to use the tool. It replied with words instead:")
        print()
        print(" ", reply["message"]["content"].strip()[:500])
        print()
        print("If this keeps happening, the model is too small to call tools reliably.")
        print("The fix is a bigger model:  ollama pull qwen3:8b")
        return

    print("The model asked to run our tool. Here is what it wants to call:")
    print()
    for call in calls:
        print("  function:", call["function"]["name"])
        given = call["function"]["arguments"]
        if isinstance(given, str):
            given = json.loads(given)
        print("  values it pulled out of that sentence:")
        for key in CUSTOMER_FIELDS:
            mark = " " if key in given else "MISSING"
            print(f"    {mark:>7}  {key:26s} {given.get(key, '')}")

        missing = [k for k in CUSTOMER_FIELDS if k not in given]
        print()
        if missing:
            print(f"  {len(missing)} field(s) missing. Step 5 is where we teach it to ask.")
        else:
            print("  Every field present. The tool could be run on this as it stands.")

    print()
    print("Step 3 done. The model knows the tool exists and chose to use it.")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# WHAT WE GAINED FROM STEP 3
# ---------------------------------------------------------------------------
# Proof that the model will reach for our tool rather than making something up,
# and a look at how well it pulls 25 separate facts out of one plain sentence.
#
# Two things to watch in the output:
#
#   1. Did it call the tool at all? If it answered in words instead, the model
#      is too small. That is a size problem, not a code problem.
#
#   2. How many fields did it get? Anything missing is what Step 5 fixes, by
#      teaching the agent to ask for what it does not have instead of guessing.
#
# We still have not RUN the tool. The model only asked. Connecting the request
# to the real function, and handing the answer back, is Step 4.
# ---------------------------------------------------------------------------
