# The interface, and why it looks like this

Written so every design choice can be defended, not just admired.

---

# The finding that shaped everything

Research on conversational interfaces reports that roughly **71% of AI products are
abandoned because of the interface, not the model underneath.**

That is worth saying out loud, because this project spent three phases proving the
model has reached the ceiling of its data. If the interface is wrong, none of that
matters. The model was never the risk.

---

# Four things decide whether people trust a chat tool

These come straight from current best-practice work on conversational UI. Each one
has a specific piece of the screen.

## 1. Capability transparency

**Can the employee tell what it does before they type anything?**

The old version opened to an empty box. An empty box tells you nothing, so people
type "hi" and feel stupid when it does not help.

**What we built:** the first screen states plainly what the assistant does, says it
needs 25 details, and offers **three real examples they can click** — assess a
customer, ask what it does, ask about the limits.

Nobody has to guess what to say.

## 2. Persistent context

**Does the employee know where they are in the process?**

The progress was previously hidden in a collapsed sidebar. Hidden progress is not
progress.

**What we built:** a progress bar directly under the header, always visible, reading
*"18 of 25 details collected"*, with an expander listing exactly what is still
missing.

This also does something more important than convenience: **it proves the assistant
is not quietly filling in blanks.** What it knows is visible rather than implied.

## 3. Confidence display

**Does it show how sure it is, or does it just assert?**

The old version returned one paragraph of prose with the risk buried in a sentence.
A number that matters should not be a word in a paragraph.

**What we built:** the risk drawn as a large figure and a bar, **with the acting
line marked on the bar itself**. Green below the line, amber just above it, red well
above it. The employee can see at a glance not just the score but how far past the
threshold it sits.

And underneath every assessment, permanently:

> About a third of customers who close their card look identical to customers who
> stay. A low score is not a guarantee.

That sentence is the honest limit from Phase 3, and putting it on the screen rather
than in the report is a deliberate choice.

## 4. Recovery

**What happens when something fails?**

**What we built:** input problems are listed as plain sentences — *"salary is 900,
outside the 2,000 to 70,000 range seen in the data. Typo?"* Unexpected errors say
*"Something went wrong and I have stopped rather than guess."*

Never a stack trace. The employee cannot fix a stack trace.

---

# The fifth thing, specific to a bank

**Tone follows context.** The research is explicit: a tool for filing insurance
claims needs a calm, steady rhythm; a fashion assistant can be informal. A retention
tool sits with money decisions, so it should feel **steady, not chatty.**

That drove:

- **Confident, not clinical.** The first attempt was all white and read like a
  hospital form. The page is now a soft blue-grey so the white cards lift off it,
  with a navy-to-teal band across the top for brand presence.
- **Colour carries meaning, never decoration.** Teal for what the customer is worth,
  amber for the expected gain, navy for the offer to act on, and red / amber / green
  for the risk itself. If something is coloured on this screen, the colour is telling
  you something.
- **Restrained avatars.** The old emoji faces looked like a toy. A small diamond and
  a dot say the same thing without the costume.
- **Space.** Generous padding, a capped width of 860 pixels, soft shadows rather than
  hard borders. Text the eye can rest on.

---

# The structural change that mattered most

The old assistant answered with **one paragraph containing everything**: risk,
reasons, value, offer.

The new one returns a **structured result** that the screen draws as separate blocks:

1. **Risk** — the number, the bar, the acting line, the verdict
2. **Why** — the reasons as a short list
3. **Worth to the bank** and **expected gain** — side by side, so the arithmetic of
   the decision is visible
4. **The offer** — in a dark card, because it is the thing the employee acts on

This needed a small change in the code: `respond()` now returns the assessment
alongside the sentence, so the screen can draw the numbers instead of burying them.
The terminal version ignores it and still works.

**Why it matters:** a marketing employee has to act on this. "Which offer" and "is
it worth it" are the two things they need in under a second. In a paragraph they are
somewhere in the middle of sentence three.

---

# What we deliberately did not do

**No dark mode.** One theme done well beats two done adequately, and light reads
better for figures.

**No animation.** Nothing here benefits from movement, and it would undercut the
calm.

**No dashboard.** It is a chat tool. Adding charts of the whole book would confuse
what it is for.

**No rewrite away from Streamlit.** The interface is not the contribution, and the
whole page is 300 lines with no logic in it. It could be replaced entirely without
touching the model, the tool, or the offers.

---

# Sources

- [Chatbot UI/UX design best practices, 2026](https://lollypop.design/blog/2025/january/chatbot-ui-ux-design-best-practices-examples/)
- [Chatbot UI design patterns and best practices, 2026](https://fuselabcreative.com/chatbot-interface-design-guide/)
- [Conversational UI patterns, 2026](https://www.parallelhq.com/blog/chatbot-ux-design)
- [UI design for AI agents, 2026](https://fuselabcreative.com/ui-design-for-ai-agents/)
- [AI chatbot UX best practices](https://www.letsgroto.com/blog/ux-best-practices-for-ai-chatbots)
- [Streamlit theming configuration](https://docs.streamlit.io/develop/concepts/custom-components/components-v2/theming)
