"""
Phase 4 — Step 4: the loop. This is the agent.

WHAT THIS STEP DOES
-------------------
Step 2 built a tool. Step 3 showed the model will ask for it. Nothing connected
those two things. This step does, and that connection is the agent.

The loop is four moves, repeated:

    1. send the conversation so far to the model
    2. if the model replied with words -> show them, done
    3. if the model asked for the tool -> run the REAL Python function
    4. put the answer into the conversation and go back to 1

That is the whole mechanism. About forty lines. No framework.

WHY WE WROTE IT OURSELVES
-------------------------
A framework would do this in one line. It would also mean that every question
about how the agent behaves has the answer "the framework does it". Here, every
question has an answer we can point at in our own code.

WHAT THE MODEL CAN AND CANNOT DO
--------------------------------
It can decide WHEN to call the tool and pull the customer's details out of a
sentence. It cannot produce a risk score, touch the model file, or do any of the
arithmetic. Those happen in Python, in step2_churn_tool.py, where we can check
them. If the model invents a number, it is not in the answer.

HOW TO RUN IT
-------------
    python agent/step4_the_loop.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama

from step2_churn_tool import assess_customer
from step3_tell_the_model import ASSESS_TOOL, CUSTOMER_FIELDS, MODEL

MAX_TURNS = 6      # a stop, so a confused model cannot loop forever


INSTRUCTIONS = """You help the bank's marketing team decide what to do about a
credit card customer who might close their card.

You have one tool: assess_customer. It is the only thing that may produce a risk
score, a customer value, or an offer. You must never produce those yourself.

Rules:
- Never invent a customer detail. If a field is missing, say which one and stop.
- After the tool answers, explain it in plain language to a marketing employee
  who is not technical. Give: the risk, the main reasons, whether the customer
  is worth keeping, and which offer to make.
- Keep it short. No bullet lists longer than four items. No jargon.
"""


# ---------------------------------------------------------------------------
# Running the tool the model asked for
# ---------------------------------------------------------------------------
def run_the_tool(call):
    """Take what the model asked for, run the real function, return the answer.

    Anything that goes wrong is turned into a plain sentence and handed back to
    the model, so it can ask the employee rather than crashing.
    """
    given = call["function"]["arguments"]
    if isinstance(given, str):
        given = json.loads(given)

    missing = [f for f in CUSTOMER_FIELDS if f not in given]
    if missing:
        return {"error": "missing information",
                "missing_fields": missing,
                "what_to_do": "Ask the employee for these before trying again."}

    try:
        return assess_customer(given)
    except Exception as error:
        return {"error": str(error),
                "what_to_do": "Tell the employee the tool failed and why."}


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------
def ask_the_agent(what_the_employee_said, show_working=True):
    """Send a message, let the model use the tool if it wants, return the reply."""

    conversation = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": what_the_employee_said},
    ]

    for turn in range(MAX_TURNS):

        # ---- 1. send everything so far ----
        reply = ollama.chat(model=MODEL, messages=conversation, tools=[ASSESS_TOOL])
        message = reply["message"]
        conversation.append(message)

        calls = message.get("tool_calls")

        # ---- 2. no tool wanted: the model is talking to us ----
        if not calls:
            return message.get("content", "").strip(), conversation

        # ---- 3. the model asked for the tool: run it for real ----
        for call in calls:
            if show_working:
                print(f"  [the model asked to run {call['function']['name']}]")

            answer = run_the_tool(call)

            if show_working:
                if "error" in answer:
                    print(f"  [tool said: {answer['error']}]")
                else:
                    print(f"  [tool said: risk {answer['prediction']['probability']}, "
                          f"worth {answer['annual_value_egp']} EGP, "
                          f"offer: {answer['recommended_offer']}]")

            # ---- 4. put the answer back into the conversation ----
            conversation.append({
                "role": "tool",
                "content": json.dumps(answer, default=str),
            })

    return "The agent went round too many times without finishing.", conversation


# ---------------------------------------------------------------------------
# Watch one full cycle
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    employee_said = (
        "Customer is 39, married with kids, private sector, earns 9000 a month, "
        "salary goes to another bank. With us 4.4 years. I-Score 640. Has a card "
        "with another bank. Took 2 loans, still owes 11610, missed a payment once. "
        "Card spending last six months: 2400, 2250, 2100, 1850, 1700, 1600. "
        "Repayments: 1850, 1700, 1600, 1400, 1300, 1200. "
        "Is he going to close the card, and what should I offer him?"
    )

    print("=" * 70)
    print("THE MARKETING EMPLOYEE SAYS")
    print("=" * 70)
    print(" ", employee_said)
    print()

    print("=" * 70)
    print("WHAT HAPPENS INSIDE")
    print("=" * 70)
    answer, conversation = ask_the_agent(employee_said)
    print()

    print("=" * 70)
    print("WHAT THE AGENT TELLS THE EMPLOYEE")
    print("=" * 70)
    print(answer)
    print()
    print(f"(the whole exchange took {len(conversation)} messages)")


# ---------------------------------------------------------------------------
# WHAT WE GAINED FROM STEP 4
# ---------------------------------------------------------------------------
# A working agent. The employee describes a customer in one sentence, the model
# decides to use the tool, our Python does the real work, and the model explains
# the result back in plain language.
#
# The division of labour is the part worth defending:
#
#   the model  - reads messy English, decides when to act, explains the answer
#   our code   - every number, every decision, every offer
#
# It is not a chatbot with opinions about churn. It is a translator sitting on
# top of a model we measured, with the judgement kept in code we can read.
#
# Still missing, and that is Step 5: it can only handle a customer described in
# one go. If a field is missing it says so and stops, instead of asking.
# ---------------------------------------------------------------------------
