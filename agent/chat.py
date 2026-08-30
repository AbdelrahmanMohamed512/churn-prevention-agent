"""
The chat window.

    .\\venv\\Scripts\\python.exe -m streamlit run agent\\chat.py

There is no thinking in this file. It calls respond() from agent.py and draws
the result. Delete it and the project still works from the terminal.

THE DESIGN, AND WHY
-------------------
Research on conversational interfaces reports that about 71% of AI products are
abandoned because of the interface, not the model underneath. Four things decide
whether people trust one, and each has a piece of this file:

  1. Capability transparency - can they tell what it does BEFORE typing?
     -> the empty state, with three real examples they can click

  2. Persistent context - do they know where they are?
     -> the progress strip, always visible, never hidden in a menu

  3. Confidence display - does it show how sure it is?
     -> the risk bar, with the acting line marked on it, and the ceiling stated

  4. Recovery - what happens when something fails?
     -> problems are listed plainly, never a stack trace

And one more, specific to a bank: confident, not clinical. The first version was
all white and read like a hospital form. This one puts a navy-to-teal band at the
top for brand presence, tints the page so the white cards lift off it, and lets
colour carry meaning - teal for money, amber for the decision, red and green for
risk. Colour is never decoration here; every coloured thing means something.
"""

import streamlit as st

from agent import NEEDED, respond

st.set_page_config(page_title="Churn Assistant",
                   page_icon="💳",
                   layout="centered",
                   initial_sidebar_state="collapsed")


# ---------------------------------------------------------------------------
# Styling. Streamlit's defaults are fine for a prototype and too loud for a bank.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  .block-container { padding-top: 1.6rem; max-width: 860px; }

  /* messages sit on the tinted page, cards lift off it */
  [data-testid="stChatMessage"] { background: transparent; padding: 0.2rem 0; }

  /* ---- the brand band at the top ---- */
  .banner {
      background: linear-gradient(120deg, #1E2761 0%, #2E3D8F 55%, #128A8A 100%);
      border-radius: 14px;
      padding: 1.4rem 1.6rem;
      color: #FFFFFF;
      margin-bottom: 1.2rem;
      box-shadow: 0 6px 18px rgba(30,39,97,0.18);
  }
  .banner h1 { font-size: 1.55rem; font-weight: 700; margin: 0 0 0.25rem 0; }
  .banner p  { margin: 0; color: #C6D2F2; font-size: 0.92rem; }
  .pill {
      display:inline-block; background: rgba(255,255,255,0.16);
      border-radius: 999px; padding: 0.2rem 0.7rem;
      font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase;
      margin-bottom: 0.6rem;
  }

  /* ---- cards ---- */
  .card {
      border-radius: 12px; padding: 1.1rem 1.25rem; margin: 0.5rem 0 0.9rem 0;
      background: #FFFFFF; border: 1px solid #E1E7F5;
      box-shadow: 0 2px 8px rgba(20,24,36,0.05);
  }
  .card-teal  { background:#E9F6F5; border:1px solid #B9E3E0; }
  .card-amber { background:#FDF3E1; border:1px solid #F2DCB0; }
  .card-navy  {
      background: linear-gradient(120deg, #1E2761 0%, #2C3A85 100%);
      color:#FFFFFF; border:none;
      box-shadow: 0 6px 18px rgba(30,39,97,0.22);
  }

  .label {
      font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
      color: #7C87A0; margin-bottom: 0.35rem; font-weight: 600;
  }
  .label-teal  { color:#0E7C7B; }
  .label-amber { color:#B87A0A; }
  .label-light { color:#A9B4D4; }

  .big   { font-size: 2.8rem; font-weight: 800; line-height: 1; }
  .unit  { font-size: 0.85rem; color: #7C87A0; }
  .headline { font-size: 1.12rem; font-weight: 700; color:#141824; }
  .quiet { font-size: 0.88rem; color:#4A5163; line-height:1.55; }
  .quiet-light { font-size: 0.88rem; color:#C6D2F2; line-height:1.55; }

  /* ---- the risk bar ---- */
  .track {
      position: relative; height: 12px; border-radius: 6px;
      background: #E4E9F4; margin: 0.9rem 0 0.4rem 0;
  }
  .fill   { position:absolute; height:12px; border-radius:6px; left:0; }
  .marker { position:absolute; top:-5px; width:2px; height:22px; background:#141824; }
  .scale  { display:flex; justify-content:space-between;
            font-size:0.72rem; color:#7C87A0; }

  /* ---- avatars ----
     Streamlit only accepts an emoji or an image for avatar=, so we leave the
     defaults in place and quieten them with CSS instead. */
  [data-testid="stChatMessageAvatarUser"] {
      background-color: #7C87A0 !important; color:#FFFFFF !important;
  }
  [data-testid="stChatMessageAvatarAssistant"] {
      background-color: #1E2761 !important; color:#FFFFFF !important;
  }

  /* ---- example buttons ---- */
  div[data-testid="stButton"] button {
      border-radius: 10px; border: 1px solid #C9D4EE; background:#FFFFFF;
      color:#1E2761; font-weight:600;
  }
  div[data-testid="stButton"] button:hover {
      border-color:#1E2761; background:#EEF2FC; color:#1E2761;
  }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Memory. Streamlit re-runs this file on every keystroke, so anything we want to
# survive has to live in st.session_state.
# ---------------------------------------------------------------------------
if "known" not in st.session_state:
    st.session_state.known = {}
    st.session_state.notes = ""
    st.session_state.chat = []        # list of (who, text, assessment or None)
    st.session_state.queued = None    # a prompt clicked from the empty state
    st.session_state.last = None      # the most recent assessment, for follow-ups


def start_over():
    st.session_state.known = {}
    st.session_state.notes = ""
    st.session_state.chat = []
    st.session_state.queued = None
    st.session_state.last = None


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="banner">
  <div class="pill">Credit card retention</div>
  <h1>Churn Assistant</h1>
  <p>Describe a customer. I work out whether they will close their card, why,
     and what to offer.</p>
</div>
""", unsafe_allow_html=True)

head_l, head_r = st.columns([5, 1])
with head_r:
    st.button("New customer", on_click=start_over, use_container_width=True)

st.write("")


# ---------------------------------------------------------------------------
# Progress. Always visible - the employee should never wonder what it has.
# ---------------------------------------------------------------------------
have = len(st.session_state.known)
total = len(NEEDED)

if st.session_state.chat:
    st.progress(have / total)
    cols = st.columns([3, 2])
    cols[0].markdown(f'<div class="quiet"><b>{have} of {total}</b> details collected</div>',
                     unsafe_allow_html=True)
    if have < total:
        missing = [NEEDED[f] for f in NEEDED if f not in st.session_state.known]
        with st.expander(f"Still needed ({len(missing)})"):
            st.markdown('<div class="quiet">' + " · ".join(missing) + "</div>",
                        unsafe_allow_html=True)
    else:
        cols[1].markdown('<div class="quiet">Ready to assess</div>',
                         unsafe_allow_html=True)
    st.write("")


# ---------------------------------------------------------------------------
# Drawing an assessment properly, instead of as a paragraph
# ---------------------------------------------------------------------------
def draw_assessment(a):
    risk = a["risk_out_of_100"]
    line = a["acting_line"]

    colour = "#C0453F" if risk >= line + 15 else "#E39A00" if risk >= line else "#3F7D68"
    verdict = "Above the line — worth acting on" if a["will_close"] \
              else "Below the line — no action needed"

    st.markdown(f"""
    <div class="card">
      <div class="label">Risk of closing the card</div>
      <div style="display:flex; align-items:baseline; gap:0.6rem;">
        <span class="big" style="color:{colour}">{risk}</span>
        <span class="unit">out of 100</span>
      </div>
      <div class="track">
        <div class="fill" style="width:{min(risk,100)}%; background:{colour}"></div>
        <div class="marker" style="left:{line}%"></div>
      </div>
      <div class="scale"><span>0</span><span>acting line {line}</span><span>100</span></div>
      <div class="quiet" style="margin-top:0.7rem"><b>{verdict}</b></div>
    </div>
    """, unsafe_allow_html=True)

    reasons = "".join(f"<li>{r}</li>" for r in a["reasons"])
    st.markdown(f"""
    <div class="card">
      <div class="label">Why</div>
      <ul class="quiet" style="margin:0.2rem 0 0 1rem; padding:0">{reasons}</ul>
    </div>
    """, unsafe_allow_html=True)

    a_col, b_col = st.columns(2)
    with a_col:
        st.markdown(f"""
        <div class="card card-teal">
          <div class="label label-teal">Worth to the bank</div>
          <div class="headline">{a['worth_per_year']:,} EGP a year</div>
          <div class="quiet" style="margin-top:0.3rem">
            {a['customer_kind'].title()} customer</div>
        </div>
        """, unsafe_allow_html=True)
    with b_col:
        st.markdown(f"""
        <div class="card card-amber">
          <div class="label label-amber">Expected gain</div>
          <div class="headline">{a['expected_gain']:,} EGP</div>
          <div class="quiet" style="margin-top:0.3rem">
            against a cost of {a['offer_cost']:,} EGP</div>
        </div>
        """, unsafe_allow_html=True)

    if a["make_the_offer"]:
        st.markdown(f"""
        <div class="card card-navy">
          <div class="label label-light">Recommended offer</div>
          <div style="font-size:1.15rem; font-weight:600; margin-bottom:0.4rem">
            {a['offer']}</div>
          <div class="quiet-light">{a['offer_fixes']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="card">
          <div class="label">Recommendation</div>
          <div class="headline">Make no offer</div>
          <div class="quiet" style="margin-top:0.3rem">
            The expected gain of {a['expected_gain']:,} EGP does not cover the
            {a['offer_cost']:,} EGP this would cost. Monitor and check again next month.</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("About a third of customers who close their card look identical to "
               "customers who stay. A low score is not a guarantee.")


# ---------------------------------------------------------------------------
# Empty state. This is the single biggest thing an employee needs: knowing what
# the tool can do before they have typed anything.
# ---------------------------------------------------------------------------
EXAMPLES = [
    ("Assess a customer",
     "Customer is 52, married with children, private sector, earns 11954 a month, "
     "salary goes to another bank. With us 2.7 years. I-Score 623. No card at "
     "another bank. Took 2 loans, owes nothing now, and has missed a payment "
     "before. Card spending over six months: 3393, 3167, 2665, 2182, 1698, 1554. "
     "Repayments: 2023, 1974, 2096, 1489, 1035, 1139."),
    ("Ask what it does", "What can you do, and how do you decide?"),
    ("Ask about the limits", "How accurate is this, and when is it wrong?"),
]

if not st.session_state.chat:
    st.markdown("""
    <div class="card">
      <div class="headline">Describe a customer in your own words.</div>
      <div class="quiet" style="margin-top:0.5rem">
        I work out whether they are likely to close their credit card, why, what
        they are worth to the bank, and which retention offer suits them — or
        whether to make no offer at all.
        <br><br>
        I need 25 details. Tell me whatever you have and I will ask for the rest.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="label">Try one</div>', unsafe_allow_html=True)
    for label, prompt in EXAMPLES:
        if st.button(label, use_container_width=True, key=f"eg_{label}"):
            st.session_state.queued = prompt
            st.rerun()

    st.caption("The language model runs on this computer. Nothing is sent over the "
               "internet. Use invented customers while testing.")


# ---------------------------------------------------------------------------
# The conversation so far
# ---------------------------------------------------------------------------
for who, text, assessment in st.session_state.chat:
    with st.chat_message(who):
        if text:
            st.write(text)
        if assessment:
            draw_assessment(assessment)


# ---------------------------------------------------------------------------
# The box you type into
# ---------------------------------------------------------------------------
typed = st.chat_input("Describe a customer, or ask me a question")

if st.session_state.queued:
    typed = st.session_state.queued
    st.session_state.queued = None

if typed:
    st.session_state.chat.append(("user", typed, None))

    with st.chat_message("user"):
        st.write(typed)

    with st.chat_message("assistant"):
        with st.spinner("Working it out..."):
            st.session_state.notes += "\n" + typed
            try:
                answer, assessment = respond(typed,
                                             st.session_state.known,
                                             st.session_state.notes,
                                             st.session_state.last)
                if assessment:
                    st.session_state.last = assessment
            except FileNotFoundError as error:
                answer, assessment = str(error), None
            except Exception as error:
                answer, assessment = (
                    f"Something went wrong and I have stopped rather than guess.\n\n"
                    f"`{error}`", None)

        if answer:
            st.write(answer)
        if assessment:
            draw_assessment(assessment)

    st.session_state.chat.append(("assistant", answer, assessment))
    st.rerun()
