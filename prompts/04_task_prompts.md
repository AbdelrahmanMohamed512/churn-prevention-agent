# Task prompts — the two jobs the model actually does

The language model is used in exactly three places in the whole project: extraction
(prompt 02), ordinary conversation, and explaining a finished assessment. Nothing else.

## just_talk — ordinary conversation

If an assessment has already run, its real numbers are passed in as context with an
explicit instruction to invent none.

```python
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
    return clean...
```

## explain — turning the tool's numbers into English

```python
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
    return clean...
```
