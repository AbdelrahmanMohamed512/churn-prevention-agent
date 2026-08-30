"""
The retention offers, and the rule for choosing one.

Twelve things the bank can give a customer to stop them closing their card,
and one plain function that picks the right one.
"""

# Each offer: what it is called, what it costs the bank, what problem it fixes.
# Costs are PLACEHOLDERS. The bank sets the real ones.

NO_OFFER = {
    "name": "No offer",
    "cost": 0,
    "fixes": "Nothing. This customer is not worth spending money on.",
}

RATE_CUT = {
    "name": "Lower the interest on their balance for 6 months",
    "cost": 500,
    "fixes": "They are struggling with what the card costs them each month.",
}

INSTALMENTS = {
    "name": "Turn their balance into 0% instalments",
    "cost": 500,
    "fixes": "They are stuck with a balance they cannot clear.",
}

SALARY_BONUS = {
    "name": "Cash bonus for moving their salary to us",
    "cost": 1000,
    "fixes": "We are their side bank, not their main one.",
}

FEE_WAIVER = {
    "name": "Waive the annual fee for a year",
    "cost": 600,
    "fixes": "They do not use the card enough to justify paying for it.",
}

CASHBACK = {
    "name": "Extra cashback in one category for 3 months",
    "cost": 400,
    "fixes": "Their other card gives them a better reason to use it.",
}

FAMILY_CARDS = {
    "name": "Free extra cards for their family",
    "cost": 150,
    "fixes": "The card is personal, so nothing in the household depends on it.",
}

MERCHANT_PLANS = {
    "name": "0% instalments at our partner shops",
    "cost": 250,
    "fixes": "The card offers nothing their other card does not.",
}


def pick_offer(customer, kind, yearly_value):
    """Choose one offer for this customer.

    customer     - the raw details
    kind         - "distressed" or "drifting", from tool.py
    yearly_value - what they are worth to the bank per year, in EGP

    Read it top to bottom. The first rule that matches wins.
    """

    # Rule 1. Too small to be worth anything. Nothing else matters.
    if yearly_value < 800:
        return NO_OFFER

    # Rule 2. A money problem. Make the card cheaper, never ask them to spend more.
    if kind == "distressed":
        if customer["outstanding_loan_balance"] > 0:
            return INSTALMENTS
        return RATE_CUT

    # Rule 3. A drifting customer. Give them a reason to use the card again.
    if customer["salary_lands_in_bank"] == 0:
        return SALARY_BONUS

    if customer["has_other_credit_cards"] == 1:
        return CASHBACK

    if customer["married"] == 1 or customer["has_dependents"] == 1:
        return FAMILY_CARDS

    if recent_spending(customer) < 900:
        return FEE_WAIVER

    return MERCHANT_PLANS


def recent_spending(customer):
    """Average card spending over the last three months."""
    last_three = [customer["purchase_month_4"],
                  customer["purchase_month_5"],
                  customer["purchase_month_6"]]
    return sum(last_three) / 3
