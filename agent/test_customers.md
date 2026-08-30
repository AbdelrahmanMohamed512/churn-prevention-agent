# Four customers to test the agent with

**These are real rows from the bank file, not invented.** So we already know what
actually happened to each one, which means you can check whether the agent is
sensible rather than just fluent.

Copy a whole block, paste it into the agent, press Enter.

---

## 1. Distressed — this customer did close their card

> Customer is 52, married with children, private sector, earns 11954 a month, salary
> goes to another bank. With us 2.7 years. I-Score 623. No card at another bank.
> Took 2 loans, owes nothing now, and has missed a payment before.
> Card spending over six months: 3393, 3167, 2665, 2182, 1698, 1554.
> Repayments: 2023, 1974, 2096, 1489, 1035, 1139.

**What to look for:** spending nearly halved, repaying only about 76 of every 100
spent, and a missed payment on record. The agent should call this **distressed** and
offer something that eases the burden — a lower interest rate, or turning the balance
into instalments. **It should not ask this customer to spend more.**

---

## 2. Drifting — this customer also closed their card

> Customer is 22, single, no children, self-employed, earns 11966 a month, salary goes
> elsewhere. With us 1.9 years. I-Score 586. Has a credit card at another bank. Never
> taken a loan, owes nothing, never missed a payment.
> Card spending over six months: 1792, 1723, 1155, 974, 1188, 826.
> Repayments: 1537, 1668, 912, 826, 1008, 672.

**What to look for:** clean payment record, no debt, but spending has more than halved
and they already hold a rival card. This is a relationship problem, not a money one.
The agent should call this **drifting** and reach for something that wins engagement
back — cashback, partner instalments, or the salary transfer bonus.

**Same risk, opposite offer to customer 1.** That contrast is the strongest thing you
can show your manager.

---

## 3. Safe — this customer stayed

> Customer is 45, married with children, self-employed, earns 4393 a month, salary is
> paid into our bank. With us 0.4 years. I-Score 679. No card elsewhere. Never taken a
> loan, owes nothing, never missed a payment.
> Card spending over six months: 1254, 1355, 1158, 1617, 1354, 1917.
> Repayments: 1094, 1324, 1051, 1321, 1171, 1780.

**What to look for:** spending is **growing**, salary is with us, no debt problems. The
agent should give a low risk and recommend **no offer**.

This is the important one to test. An agent that always finds something to give is
broken. Spending money on this customer is pure waste.

---

## 4. The invisible one — this customer left, and nothing warned us

> Customer is 34, single, no children, private sector, earns 4529 a month, salary is
> paid into our bank. With us 12.8 years. I-Score 706. No card elsewhere. Took 2 loans,
> still owes 17150, never missed a payment.
> Card spending over six months: 915, 934, 1053, 1062, 1225, 1287.
> Repayments: 807, 861, 836, 845, 1176, 1059.

**What to look for:** the agent will probably say **low risk** — and it will be wrong,
because this customer did close their card.

**That is not a bug, and it is the most honest thing in the whole demo.** Spending is
growing, the payment record is clean, twelve years with the bank, salary with us.
Nothing in the file says they were going to leave.

This is the group Phase 3 measured: about a third of the customers who leave look
identical to customers who stay. Notice the loan balance of 17,150 on a 4,529 salary —
the report's guess is that people like this refinanced elsewhere, and the bank would
need loan closure records to test it.

**Show this one to your manager on purpose.** It proves you know where the model
stops, rather than pretending it does not.

---

# Testing it a piece at a time

The agent is supposed to ask for what it does not have. Give it half a customer and
watch:

> I have a customer, 52, married with kids, private sector, earns 11954

It should ask for a few of the missing details, not all twenty-five at once, and not
invent any. Then feed it the rest:

> salary goes to another bank, 2.7 years with us, I-Score 623, no other card

Then:

> 2 loans, owes nothing, missed a payment once. Spending: 3393, 3167, 2665, 2182,
> 1698, 1554. Repayments: 2023, 1974, 2096, 1489, 1035, 1139

Watch the `[x of 25 details collected]` counter climb. When it reaches 25 the agent
runs the tool by itself.

---

# What a good answer looks like

1. A risk out of 100, and whether that is above the line for acting
2. Two or three plain reasons, not a list of column names
3. What the customer is worth to the bank in a year
4. One offer, with the reason it suits this particular customer
5. Or **no offer**, when the customer is not worth the spend

If it produces a risk score without calling the tool, that is a failure — say so.
Only the tool is allowed to produce that number.
