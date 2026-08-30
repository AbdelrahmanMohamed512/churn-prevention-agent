# What the model leans on

Logistic regression is a scorecard. Every input is scaled, multiplied by a fixed weight,
and the results are added up. So the weights ARE the explanation — there is nothing to
approximate, and no SHAP was needed.

These are the absolute standardised coefficients recorded in `docs/EXPERIMENT_LOG.md`.
All **MEASURED**.

```
  purchase_volatility            0.361
  slope_x_relationship_depth     0.303
  slope_x_purchase_volatility    0.252
  slope_x_recent_purchases       0.251
  spend_to_salary                0.167
  payment_ratio                  0.067
  purchase_slope                 0.054
  recent_purchases               0.025
```

## Reading it

**purchase_volatility is the single strongest input.** Erratic spending — big month, small
month, big month — predicts closing better than the spending level itself. A steady spender
is a settled customer.

**Three of the top four are interaction terms.** `slope_x_...` means the spending trend
multiplied by something else. This says the direction of spending only matters *in
context*: a falling slope on a deep relationship means something different from a falling
slope on a thin one. Alone, `purchase_slope` scores only 0.054 — nearly nothing. Combined,
its interactions score 0.303, 0.252 and 0.251. That is the main finding of the feature
engineering work.

**spend_to_salary at 0.167** is the strongest single non-interaction feature after
volatility. Spending a large share of salary on a card is strain.

**recent_purchases at 0.025 is almost ignored.** How much someone spends recently, on its
own, tells the model very little. The change matters, the level does not.

## The raw signal behind it

Measured directly from the data, closures per 100 customers by how far spending fell over
the six months:

fell more than 30%: 70.0 closed per 100.
fell 20–30%: 42.0.
fell 10–20%: 28.1.
fell 5–10%: 19.1.
roughly flat: 13.4.
growing: 6.9.

From 48.6 down to 3.9 across the extremes of the spending-trend feature. This is the
strongest single relationship in the dataset.

## How the slope is calculated

Not the difference between month one and month six — that throws away four months and
breaks on a single odd month.

A straight line is fitted through all six points using least squares: for any candidate
line, measure the vertical gap from each of the six actual points to the line, square each
gap, add the six squares together, and keep the line where that total is smallest. The
slope of that winning line is the feature. In code: `np.polyfit(months, values, 1)[0]`.

Squaring is what makes it work — it removes the sign so gaps above and below the line both
count, and it punishes one large miss more than several small ones.

## NOT RECORDED

- Coefficient signs (positive or negative direction) — only absolute values were logged.
- Coefficients for the remaining features in the pipeline beyond these eight.
- Confidence intervals or standard errors on any coefficient.
