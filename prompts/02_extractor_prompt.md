# Extractor prompt — pulling fields out of a sentence

A deliberately tiny, separate prompt used ONLY when reading customer details out of
what the employee typed. Lives in `agent/agent.py` as `EXTRACTOR`.

## Why it is separate — this was a real bug

The first version sent the full system prompt on the extraction call too. The model
started trying to be an assistant instead of filling in a form, and returned no fields
at all. One job per prompt.

```
You read text and call the given function with any values you find.              You do not chat, explain, or ask questions.
```

### The user message that accompanies it

```
Call assess_customer with every value you can find in these notes about one bank
customer. Do not guess. Notes:
<everything the employee has typed so far>
```
