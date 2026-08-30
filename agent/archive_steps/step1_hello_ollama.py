"""
Phase 4 — Step 1: can Python talk to Ollama?

WHAT THIS STEP DOES
-------------------
Nothing about churn. Nothing about customers. It sends one sentence to the
language model running on this computer and prints what comes back.

WHY IT IS WORTH A WHOLE STEP
----------------------------
Everything after this depends on Python being able to reach Ollama. If that
link is broken, Step 4 would fail with a confusing error and we would not know
whether the problem was the agent, the tool, the model, or the connection.

So we check the connection on its own, once, while there is nothing else that
could possibly be wrong.

HOW TO RUN IT
-------------
    pip install ollama
    python agent/step1_hello_ollama.py
"""

import ollama

# The model we are talking to. Change this one line if you pull a different one.
# qwen3:4b  — about 2.5 GB, runs in roughly 4 GB of memory. Our choice.
# qwen3:8b  — about 5.2 GB, more dependable at tool calling if the machine allows.
MODEL = "qwen3:4b"


def main():
    # --- 1. Is Ollama running at all? ---
    # ollama.list() asks the program on this computer which models it has.
    # If Ollama is not running, this raises an error and we say so plainly.
    try:
        installed = ollama.list()
    except Exception as error:
        print("Could not reach Ollama.")
        print("Open a terminal and run:  ollama serve")
        print()
        print("The exact error was:", error)
        return

    names = [m.model for m in installed.models]
    print("Ollama is running. Models on this computer:")
    for n in names:
        print("   ", n)
    print()

    # --- 2. Is the model we want actually here? ---
    if not any(n.startswith(MODEL.split(":")[0]) for n in names):
        print(f"'{MODEL}' is not installed yet.")
        print(f"Run this in a terminal, then try again:  ollama pull {MODEL}")
        return

    # --- 3. Send one message and print the reply ---
    # "messages" is a list of turns in a conversation. Right now there is one
    # turn: us. "role" says who is speaking. "content" is what they said.
    # This same shape carries the whole conversation later on.
    print(f"Asking {MODEL} to say hello...")
    print()

    reply = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "user",
             "content": "Say hello in one short sentence. No thinking out loud."}
        ],
    )

    print("The model replied:")
    print("   ", reply["message"]["content"].strip())
    print()
    print("Connection works. Step 1 done.")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# WHAT WE GAINED FROM STEP 1
# ---------------------------------------------------------------------------
# A proven link between Python and the language model on this computer, and the
# three lines of code the rest of Phase 4 is built on:
#
#   - ollama.chat(model=..., messages=[...])  sends a conversation
#   - each message is {"role": ..., "content": ...}
#   - reply["message"]["content"]             is what the model said back
#
# Everything from here is the same call with more in the "messages" list, plus
# one extra argument in Step 3 that tells the model our tool exists.
#
# Also worth recording for the report: nothing in this step left the computer.
# That is the whole reason for using Ollama, and it removes the warning in the
# project plan about never typing real customer data into a hosted service.
# ---------------------------------------------------------------------------
