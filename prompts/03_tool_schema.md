# Tool schema — what the model is told it can call

Built in `agent/agent.py` as `TOOL_FORM`. One function, `assess_customer`, with all
25 customer fields as parameters. This is the entire mechanism that makes it an agent
rather than a chatbot: the model can reply with a request to call this function, and
our Python then runs the real thing.

```python
TOOL_FORM = {
    "type": "function",
    "function": {
        "name": "assess_customer",
        "description": "Assess a credit card customer. Fill in every value you can find.",
        "parameters": {
            "type": "object",
            "properties": {name: {"type": "string", "description": ask}
                           for name, ask in NEEDED.items()},
            "required": [],
        },
    },
}
```

"## The 25 fields, with the plain-English way each is asked for

```
age                          their age
married                      whether they are married
has_dependents               whether they have children
employment_sector            where they work: Private, Government or Self-Employed
salary                       monthly salary
salary_lands_in_bank         whether their salary is paid to us
loyalty_years                years with the bank
iscore                       their I-Score credit score
has_other_credit_cards       whether they have a card at another bank
had_loan_ever                whether they ever took a loan
number_of_loans              how many loans
outstanding_loan_balance     how much they still owe
missed_loan_payment_ever     whether they ever missed a payment
purchase_month_1..6           card spending in month N
payment_month_1..6            card repayment in month N
```
