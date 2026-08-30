"""
Phase 4 — Step 7: the chat window.

WHAT THIS STEP DOES
-------------------
Puts a proper chat box on the agent, so a marketing employee types into a web
page instead of a black terminal.

It is thirty lines of layout and nothing else. Every piece of thinking already
exists: the tool is Step 2, the offer decision is customer_value.py, and the
conversation is the Interview class in Step 5. This file only draws it.

That is deliberate, and worth saying out loud: the interface is not the
contribution. If this file were deleted the project would still work from the
terminal.

HOW TO RUN IT
-------------
This one does NOT run with the green play button, because Streamlit needs its own
command. In the VS Code terminal:

    streamlit run agent/step7_chat_window.py

A browser tab opens by itself. Press Ctrl+C in the terminal to stop it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from step3_tell_the_model import CUSTOMER_FIELDS
from step5_the_interview import Interview

st.set_page_config(page_title="Churn Assistant", page_icon="💳", layout="centered")


# ---------------------------------------------------------------------------
# Memory that survives between clicks
#
# Streamlit re-runs this whole file every time you type something. Anything not
# kept in st.session_state would be forgotten. So the conversation lives there.
# ---------------------------------------------------------------------------
if "interview" not in st.session_state:
    st.session_state.interview = Interview()
    st.session_state.history = []

interview = st.session_state.interview


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------
st.title("Churn Assistant")
st.caption(
    "Describe a credit card customer. I will ask for anything missing, then "
    "tell you the risk and which offer to make."
)

with st.sidebar:
    st.subheader("Progress")

    have = len(CUSTOMER_FIELDS) - len(interview.missing())
    st.progress(have / len(CUSTOMER_FIELDS))
    st.write(f"**{have} of {len(CUSTOMER_FIELDS)}** details collected")

    if interview.known:
        with st.expander("What I know so far"):
            for field, value in interview.known.items():
                st.write(f"`{field}` = {value}")

    if interview.missing():
        with st.expander("What I still need"):
            for field in interview.missing():
                st.write(f"- {field}")

    st.divider()
    if st.button("New customer", use_container_width=True):
        st.session_state.interview = Interview()
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption(
        "The language model runs on this computer. Nothing is sent over the "
        "internet. Even so, use invented customers while testing."
    )


# ---------------------------------------------------------------------------
# The conversation so far
# ---------------------------------------------------------------------------
for who, text in st.session_state.history:
    with st.chat_message(who):
        st.write(text)


# ---------------------------------------------------------------------------
# The box you type into
# ---------------------------------------------------------------------------
typed = st.chat_input(
    "e.g. customer is 39, married with kids, private sector, earns 9000"
)

if typed:
    st.session_state.history.append(("user", typed))
    with st.chat_message("user"):
        st.write(typed)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = interview.say(typed)
            except FileNotFoundError as error:
                answer = str(error)
            except Exception as error:
                answer = f"Something went wrong: {error}"
        st.write(answer)

    st.session_state.history.append(("assistant", answer))
    st.rerun()


# ---------------------------------------------------------------------------
# WHAT WE GAINED FROM STEP 7
# ---------------------------------------------------------------------------
# Something a marketing employee could actually be handed.
#
# The sidebar is the part worth showing. It lists exactly which details have been
# collected and which are still missing, so the employee can see the agent is not
# quietly filling in blanks. What the agent knows is visible, not implied.
#
# No logic lives in this file. It draws the Interview class from Step 5 and
# nothing more. Delete it and the project still runs from the terminal - which is
# the right shape for a project where the interface was never the point.
# ---------------------------------------------------------------------------
