# Confusion matrix

At the chosen threshold of 0.255, across all 8,500 customers, five-fold cross-validated.

```
                        predicted stay    predicted close
  actually stayed            5,612              1,191        6,803
  actually closed              599              1,098        1,697
                             6,211              2,289        8,500
```

## Which of these are real

**MEASURED** — written into `docs/EXPERIMENT_LOG.md` at the time:

- churners caught (bottom right): **1,098**
- churners missed (bottom left): **599**
- total churners: **1,697**, total stayers: **6,803**, total customers: **8,500**

**DERIVED** — arithmetic on the measured F1 of 0.5509 and the counts above. Never printed
during the project:

- false alarms (top right): **1,191**
- correctly left alone (top left): **5,612**
- total flagged: **2,289**

The derivation: recall is 1,098 ÷ 1,697 = 0.6470. F1 = 2PR ÷ (P+R), so precision =
F1 × R ÷ (2R − F1) = 0.4796. Total flagged is 1,098 ÷ 0.4796 = 2,289, so false alarms are
2,289 − 1,098 = 1,191, and correctly left alone is 6,803 − 1,191 = 5,612.

## What each box costs the bank

**599 missed churners.** These people close and were never flagged. This is the expensive
box, and the ceiling test says a large part of it is unfixable — their reason for leaving
is not in the data.

**1,191 false alarms.** These people were never going to leave and get an offer anyway.
This is why the agent exists: a retention offer to someone worth 600 EGP a year loses
money even when the risk score is right. The agent's `NO_OFFER` rule is what protects
this box, not the model.

**1,098 caught.** The only box that can produce value, and only if the offer actually
changes the decision — which this project cannot measure. See the limitations section of
`PROJECT_SUMMARY.md`.

The threshold of 0.255 was chosen to maximise F1, which balances the two error boxes.
Moving it down catches more of the 599 and inflates the 1,191. Moving it up does the
reverse. The right setting depends on the real cost of an offer, which is **NOT RECORDED** —
the bank has not supplied it.
