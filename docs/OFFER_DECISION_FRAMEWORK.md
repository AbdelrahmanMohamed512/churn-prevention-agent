# Is this customer worth a retention offer?

Answering the manager's first question, and the offer catalogue that answers the second.

Everything here is computed from `data/raw/bank_churn_dataset.csv`. Assumptions are
labelled as assumptions.

---

# 1. The finding that makes this question necessary

The model answers one question: **will this customer close their card?**

It says nothing at all about a second question: **would it be worth paying to stop them?**

Those are different, and the gap between them is large.

Take the riskiest fifth of the book — 1,700 customers, closing at 47 per 100. Inside
that single group, the annual value of a customer runs:

- the bottom tenth → about **806 EGP a year**
- the middle → about **2,284 EGP a year**
- the top tenth → about **6,856 EGP a year**

**The most valuable customer in the high-risk group is worth roughly eight and a half
times the least valuable one.** They carry the same risk score, and treating them the
same way is how a retention budget gets wasted.

And risk does not stand in for value. Across the whole book the relationship between
declining spend and customer value is **0.19** — close to nothing. The safest fifth of
customers are the *most* valuable, at a median of 4,196 EGP a year against 2,284 for
the riskiest.

**So the model cannot be used on its own to decide who gets an offer.** Something has
to sit between the prediction and the money.

---

# 2. The rule

An offer is worth making when what we expect to gain is bigger than what it costs.

**Expected gain = risk × saveability × annual value**

In plain words: how likely they are to leave, multiplied by how likely we are to change
their mind, multiplied by how much they are worth to us in a year.

Make the offer when that number is larger than the cost of the offer.

Three inputs. We have a real measurement for one, a reasonable estimate for the second,
and only a judgement for the third. Being honest about which is which is the point.

## 2.1 Risk — measured

Straight from the model. A number between 0 and 1.

This is the only one of the three we can defend with evidence, and Phase 3 proved it is
as good as this data allows: AUC 0.807.

## 2.2 Annual value — estimated

Four revenue lines, all computable from columns we already have:

**Interchange.** The bank earns a small percentage of everything spent on the card.
Six months of spending doubled gives the annual figure. Median annual spend on this
book is **17,078 EGP**.

**Interest on the carried balance.** The largest line by far. `payment_ratio` is how much
of their spending a customer pays back. **Every single customer in this dataset repays
less than they spend** — the median repays 87 of every 100. What is left over carries,
and carries interest. Median carried balance: **2,149 EGP a year**.

**Loan margin.** The bank's margin on `outstanding_loan_balance`.

**Deposit margin.** If `salary_lands_in_bank` is 1, the bank has their salary to lend
against.

Adding those four gives an annual value per customer. Across the book:

- the bottom tenth → about **615 EGP**
- the middle → about **2,568 EGP**
- the top tenth → about **6,143 EGP**
- the top one per cent → about **11,117 EGP**

**The rates behind these are placeholders.** Interchange, card interest, loan margin and
deposit margin are all set by the bank, and card interest in Egypt in particular is a
number we should not be guessing at. They sit at the top of `agent/customer_value.py` as
four named constants so the manager can replace them in one place and every figure below
updates.

## 2.3 Saveability — a judgement, and we should say so

This is the honest weak point, and it is the same limitation already recorded in the
report as **uplift modelling**.

Predicting who *will* leave is not predicting who *can be saved*. Some customers leave
no matter what you offer. A few leave *because* you contacted them and reminded them the
card exists. Separating those groups needs an experiment — deliberately leaving some
at-risk customers alone and comparing — and we have no such data.

So saveability cannot be measured here. What we can do is stop pretending it is uniform,
using two findings from Phase 1:

**The two customer types.** Distressed customers have a money problem: spending down 33%,
11,610 EGP of loans, age 39. Drifting customers have a relationship problem: spending
down 20%, 6,094 EGP of loans, age 33, and 54% already hold a rival card. Same risk score,
opposite correct response. A fee waiver will not rescue someone drowning in debt, and a
lower interest rate is meaningless to someone who simply forgot the card exists.

**The invisible third.** About 599 of the leavers look statistically identical to
customers who stayed — barely declining, and with a *better* payment record than the
average stayer. Whatever is pulling them away is not in this file. Assuming an offer will
reach them is not supported by anything.

The suggestion is three plain bands, clearly labelled as a working assumption for the
manager to overrule:

- distressed, and still banking with us → **higher chance of being saved**
- drifting, with a rival card already → **moderate**
- flagged but showing none of the usual signs → **low**

---

# 3. What this looks like in practice

Four customers, all flagged by the model, all handled differently.

**A customer worth 6,800 EGP a year, distressed, salary with us.**
High value, plausible to save, and the reason is visible. Worth a real offer — an
interest reduction or converting the balance to instalments. Even an expensive offer
pays for itself.

**A customer worth 800 EGP a year, drifting, rival card.**
The cheapest offer in the catalogue costs 150 EGP. Even at a generous save rate the
arithmetic barely works, and most of the time it loses money. **Monitor, do not spend.**

**A customer worth 4,000 EGP a year, salary paid elsewhere.**
The salary transfer bonus. This is the one offer in the catalogue that changes the
customer's relationship with the bank rather than just discounting the product, and the
underlying finding is the strongest actionable one in the analysis: 29 closures per 100
when the salary is elsewhere, 13 when it is with us.

**A customer worth 5,000 EGP a year, showing none of the usual warning signs.**
High value, so tempting. But this is the invisible group, and we have no evidence any
offer reaches them. Flag for a human to call rather than firing an automated discount at
them.

---

# 4. The offer catalogue

Twelve offers, in `agent/offers.json`. Every one is either standard international card
retention practice or a feature Egyptian banks actually run.

**On the market:** the dataset is Egyptian. The `iscore` column matches I-Score, Egypt's
credit bureau, whose scores run roughly 400 to 850 — our data runs 385 to 850. Salaries
run 2,000 to 69,790 a month, with a median of 7,046. So the offers are drawn from what
CIB and NBK actually market, not from American travel-rewards cards.

## The four price levers

1. **Annual fee waived for one year** — the most common retention offer anywhere, and the
   most often accepted.
2. **Annual fee halved** — the cheaper opening move.
3. **Lower interest on the carried balance** — for distressed customers only. Expensive,
   because interest is the largest revenue line on this book.
4. **Convert the balance to 0% instalments over 6 to 12 months** — for the heaviest
   revolvers. Closing the card does not clear the balance, so the real problem is the
   monthly burden, not the card.

## The four engagement levers

5. **Statement credit for hitting a spending target** — for drifting customers with a
   clean payment record. **Never for a distressed customer.** Asking someone under
   financial pressure to spend more is the wrong offer and arguably a harmful one.
6. **Boosted cashback in one category for three months** — to win back share from a rival
   card. CIB runs up to 25% in specific categories.
7. **0% instalments at partner merchants** — the most heavily marketed card benefit in
   Egypt. A competitive feature rather than a giveaway, so it is cheap to offer widely.
8. **Double points for six months** — for long-tenured customers. Costs nothing unless
   they spend.

## The three relationship levers

9. **Cash bonus for moving the salary across** — the strongest offer in the catalogue,
   and the only one that changes the relationship rather than discounting the product.
10. **Credit limit increase** — high credit score and clean record only. Never to someone
    under pressure. *The dataset has no credit limit column, so this one cannot be used
    properly until the bank supplies it.*
11. **Free supplementary cards** — for married customers or those with dependants.
    Deliberately creates the household commitments that hold a card in place: 29 closures
    per 100 for single with no children, 16 for married with children.

## And one that is not an offer

12. **No offer — monitor only.**

This has to stay in the list. **An agent that always has something to give will always
give something.** In a real retention programme the most common correct answer is "not
this customer", and if the catalogue has no way to say that, the agent will never say it.

## Escalation

Where several offers fit, the agent proposes the **cheapest one that addresses the actual
reason**, and holds the expensive ones back. The order is in the file.

---

# 5. What still needs the manager

1. **The four rates** — interchange, card interest, loan margin, deposit margin. Every
   value figure above moves with these.
2. **The real cost of each offer.** Ours are placeholders.
3. **Is it worse to miss a leaver or waste an offer?** This was already open question 5.
   It sets the threshold, and it is a business decision, not a modelling one.
4. **Does the bank have a save-rate figure** from past campaigns? That would replace our
   judgement on saveability with a measurement.
5. **The credit limit column**, without which utilisation cannot be computed and one
   offer stays unusable.
6. **Is anything on this list not actually approved?** The catalogue is built from public
   market practice, not from the bank's own product sheet.
