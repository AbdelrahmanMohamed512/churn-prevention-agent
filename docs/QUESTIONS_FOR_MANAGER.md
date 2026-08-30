# Questions for my manager

A running list. Add to it whenever something comes up; tick things off after the daily meeting and write the answer underneath.

---

## Open — ask at the next meeting

### 1. Do I create the retention offers, or will the bank give me the list?

**Why I'm asking:** the agent picks an offer for each customer. I need to know whether the list of possible offers is mine to design or fixed by the bank.

**Either answer works for the project** — the offers are just data the agent reads. But it changes what I say in the report, so I'd rather not guess.

**Follow-ups if they give me the list:**

- Is there a cost or value attached to each offer, or just names?
- Are there eligibility rules — offers only certain customers can receive?
- Is there a limit on how much can be offered to one customer?

**Answer:**

---

### 2. ANSWERED — Is this about all bank customers, or only credit card holders?

**Answer: churn means the customer closed their credit card.** They remain a customer of the bank; they have ended this one product.

**What this changes:** the monthly purchase and payment columns are card activity, so declining card use leading to closing the card is a coherent story rather than a coincidence. `has_other_credit_cards` becomes direct competition for this specific product. And every offer is a card retention offer — nothing is about keeping the customer at the bank, because they are not leaving it.

**Still outstanding:** does the dataset include the credit limit? I have purchases and payments but no limit, so I cannot compute utilisation, which is usually one of the stronger signals in card data.

---

### 3. Over what period was the card closure measured?

**Why I'm asking:** I now know churn means the card was closed. What I still need is the window — did they close it within three months of these six, within a year, or at any point afterwards?

It decides how much warning the model can give. Knowing somebody will close their card eventually is far less useful to the marketing team than knowing they will close it next month, and I need to state which one I am predicting.

**Answer:**

---

### 4. How recent is the data, and what period does it cover?

**Why I'm asking:** if it's several years old, the behaviour patterns may not hold today. It's a limitation I should state rather than have pointed out to me.

**Answer:**

---

### 5. Is it worse to miss a leaver, or to waste an offer on someone who was staying?

**Why I'm asking:** this decides how I tune the model. If missing a leaver is worse, I catch more people and accept some false alarms. If wasted offers are expensive, I only flag the ones I'm confident about. I can't optimise for both, and picking without asking would be me inventing the bank's priorities.

**Answer:**

---

### 6. Who is the audience for the final presentation, and how technical are they?

**Why I'm asking:** it decides how much of the modelling detail goes in the slides versus the report.

**Answer:**

---

### 7. Can customer data be typed into a third-party AI service, or must the demo use invented customers?

**Why I'm asking:** the model itself trains entirely on my machine — the dataset never leaves it. But the agent's conversation goes to Google's API, so whatever the marketing user types into the chat leaves the bank.

On the free tier, Google may use submitted content to improve its products and human reviewers may see it. On the paid tier it does not, and that costs only a few dollars for a project this size.

**My plan unless told otherwise:** use invented customers for all development and for the demo. A fabricated customer demonstrates the system exactly as well as a real one. If real records are required, I'll move to the paid tier first.

**Answer:**

---

### 8. When was each column measured — during the six months, or after the customer left?

**Why I'm asking:** if a column was recorded *after* someone left, it may be describing the consequence of leaving rather than something that predicts it. Using it would make my model look excellent and be worthless in practice.

**This worry has largely dissolved now that churn means closing a card rather than leaving the bank.** Closing a credit card does not stop a salary arriving — the customer still banks with us. So `salary_lands_in_bank` cannot be a by-product of the outcome in the way I originally feared.

**My earlier test agrees.** If the column were merely recording the outcome, almost every leaver would show no salary arriving. In fact 594 of the 1,697 — 35% — still had their salary landing with us. I also checked that no customer has a zero in any of the twelve monthly columns, so the six-month window sits entirely before the closure.

**What I still need confirmed:** the date each column was measured, particularly `salary_lands_in_bank`, `has_other_credit_cards`, `missed_loan_payment_ever` and `loyalty_years`.

**Answer:**

---

### 9. Is there anything the agent must never do or say?

**Why I'm asking:** banks usually have rules about promising things to customers. If there are constraints, I'd rather build them in than retrofit them.

**Answer:**

---

## Answered

*(move questions here with their answers once resolved)*
