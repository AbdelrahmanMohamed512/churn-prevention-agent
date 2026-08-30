# Churn Prevention Agent — project summary

Where the project stands, what has been decided, and what happens next.

---

## 1. What we are building

A chat assistant for a bank's marketing team.

A marketing employee describes a credit card customer. A machine learning model predicts whether that customer is likely to close their card, and explains what is driving that risk. The agent reads those reasons and proposes a retention offer aimed at the specific reason — not a generic one.

**Churn here means the customer closed their credit card.** They remain a customer of the bank; they have ended this one product. Everything follows from that: the monthly columns are card activity, and every offer is a card retention offer.

**One agent, one tool.** The agent is a loop written directly against a language model API. Its only tool is a Python function wrapping the trained model, which returns a prediction, a probability, and the reasons behind it.

---

## 2. The two halves, and where they meet

**The model half is statistics.** It learns from past customers what closing a card looks like, and can say "this one probably will, and here is what makes me think so." It cannot talk and knows nothing about offers.

**The agent half is language.** It talks to the marketing person, collects the details it needs, and decides what to do with the model's answer. It cannot predict anything by itself.

They meet at **a single Python function**, `predict_churn`. That function is the entire interface between them, which is why it was designed before either half was built.

---

## 3. Decisions made, and why

### The technology

| Decision | Reason |
|---|---|
| Python throughout | The machine learning libraries only exist for it, and one language means no glue between the halves |
| XGBoost for the model | The data is a table of mixed types, and the effects are combinations rather than straight lines. Trees find those; simpler models cannot without being told |
| SHAP for explanations | Gives the reasons behind one specific prediction, so every offer traces to a number rather than the agent's guesswork. It also has an exact, fast method for tree models |
| No agent framework | The tool-use loop is about forty lines. Owning it means every question about the agent's behaviour has an answer in our own code, not "the framework does it" |
| Google Gemini API | Free tier, and it supports function calling — which is the entire mechanism the agent depends on |
| Streamlit for the interface | A chat window in about thirty lines. The interface is not the contribution, so it should cost the least time |
| Google Colab for the notebooks | No local setup to fight with, and the work is accessible from anywhere |

### The data

| Decision | Reason |
|---|---|
| Build trend columns from the six monthly columns | Any single month barely separates the two groups. The change between them separates them enormously |
| Keep the trend as a number, not a yes/no flag | A steep fall is far more dangerous than a gentle one; a flag throws that away |
| Remove `customer_id` | An identifier, not a fact about the person |
| Remove `gender` | It separates nobody, even in combination with family situation. And using gender in decisions about credit or offers is restricted under banking regulation, so even a real effect could not be acted on |
| Remove `is_paying_old_loan` | An exact duplicate of "balance above zero", with no exceptions in 8,500 customers. The balance says the same thing and adds the amount |
| Split into train and test before anything else | If information from the test customers reaches training, the reported score is fiction |
| Handle the 20/80 imbalance by weighting, not by inventing fake customers | Synthetic rows add noise and produce nonsense for yes/no columns. Weighting is simpler and honest |
| Never judge the model on accuracy | With one in five closing their card, "nobody ever closes" scores 80% and is useless |
| State the model's ceiling openly | Roughly a quarter of those who closed their card are indistinguishable from those who kept it. Recall cannot exceed that, and the explanation is worth more than the missing points |

---

## 4. What the data told us

### The main finding

Any single month of spending tells you almost nothing — customers who closed their card and those who kept it look the same. But across six months the two groups start together and pull steadily apart. **The information is in the direction of travel, not the level.**

That column did not exist in the file. It had to be built, and it is the strongest signal we have by a wide margin.

### Findings worth carrying into the report

**Where the salary is paid matters most among the fixed facts** — and unlike the others it suggests an action rather than just describing a customer. That makes it the basis of an offer.

**Salary itself predicts nothing.** High and low earners close their cards at the same rate. Closing a card is not about affordability, it is about engagement.

**Two factors can mean far more together than apart.** Declining spend alone is a moderate signal; having missed a loan payment alone is mild; both together is severe. That is why a tree-based model was the right choice.

**There are two distinct kinds of customer who close a card.** One is in financial difficulty — older, carrying a large loan, has missed payments, spending collapsing because they cannot afford it. The other is younger, has never missed a payment, is paid by a different bank and already holds a competitor's card. They were never really ours. **The same risk score demands opposite offers**, and this is the single strongest justification for an agent that reasons rather than a table that looks up.

**A weak correlation can hide a real signal.** iScore looked useless as a single number, and shows a clean gradient when viewed in bands. Correlation only measures how well a straight line fits.

### Three ideas we tested and rejected

Recorded deliberately, because reporting only the successes is how people mislead themselves.

- **Gender might matter for a married man with children.** It does not — once family situation is known, gender adds nothing. But the reasoning pointed at household responsibility, which does matter, and produced a new column.
- **Payments falling faster than purchases signals distress.** No pattern.
- **A steepening fall means departure is nearer.** No pattern.

### What we checked that could have ruined the project

**Leakage.** We suspected `salary_lands_in_bank` might be recording the outcome rather than predicting it. The method: assume the worst case, work out what the data would look like if it were true, then check. It was not. The worry dissolved further once we learned churn means closing a card — closing a card does not stop a salary arriving.

**Overlap.** Two loan columns turned out to be the same column. Not cheating, but it would have split the model's reasoning across one duplicated idea and made our explanations repeat themselves.

---

## 5. Where the project stands

| Phase | Status |
|---|---|
| Understanding the data | **Done** |
| Building the new columns | **Done** — 3 removed, 11 built, each tested |
| Training the model | Next |
| Connecting it to the agent | Not started |
| Testing and write-up | Not started |

**Built so far:** a project structure with everything documented, a running exploration notebook, a working chart script, a question log for the manager, a slide deck on the exploration, and this summary.

**The dataset:** started at 29 columns, three removed, eleven built, now 38 columns across 8,500 customers.

---

## 6. What is still open

**For the manager:**

1. Over what period was the card closure measured? Decides how much warning the model can give.
2. Do I design the offers, or does the bank supply them?
3. Is the credit limit available? Without it we cannot measure how close customers are to their limit.
4. Is it worse to miss someone who closes their card, or to waste an offer on someone who was staying? This decides how the model is tuned and is not ours to invent.
5. Was any retention campaign running during these six months?
6. Does the bank hold loan closure records? A small group of the best customers closed their cards while spending more than ever, and their loan balances are unusually high — the hypothesis is that they refinanced elsewhere.

**For us:**

- Whether to keep the twelve raw monthly columns now that the trend columns exist. Test both, keep whichever works better, write down the answer.
- Two of the eleven new columns are weak and need a reason to stay.
- What extra data would catch the quarter we cannot see. Complaints, app activity, branch visits and competitor offers are the candidates, and proposing them is a genuine recommendation for the bank.

---

## 7. Next step

Split the data, build a simple baseline model so there is something to beat, then train the real one and check it honestly — with precision and recall, never accuracy.
