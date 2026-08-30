# About these plots

No plots were saved to file during the original modelling work — it ran in Google Colab
and the figures were displayed in the notebook, not written to disk.

Every image here was **re-drawn from the numbers recorded in `docs/EXPERIMENT_LOG.md`**.
They are faithful to the recorded values and nothing has been invented, but they are not
screenshots of an original training run.

| file | based on |
|---|---|
| `model_comparison.png` | MEASURED — the survey-stage AUC table |
| `feature_importance.png` | MEASURED — the eight recorded coefficients |
| `calibration.png` | MEASURED — recorded predicted-vs-actual deciles |
| `learning_curve.png` | MEASURED — recorded AUC at five training sizes |
| `closure_by_spending_fall.png` | MEASURED — recorded closure rates by band |
| `confusion_matrix.png` | **DERIVED** — see `confusion_matrix.md` |

To regenerate a real ROC curve, precision-recall curve, or per-fold breakdown, re-run
Phase 3 of `notebooks/churn_analysis.ipynb` against the original dataset. Those were never
recorded and are not reproduced here.
