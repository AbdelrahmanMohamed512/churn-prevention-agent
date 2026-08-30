import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("/sessions/trusting-beautiful-babbage/mnt/uploads/bank_churn_dataset 1.csv")

def plot_monthly_trend(df):
    months = [f"purchase_month_{i}" for i in range(1, 7)]
    stayed = df[df.churned == 0][months].mean()
    left   = df[df.churned == 1][months].mean()

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(range(1, 7), stayed.values, marker="o", lw=2.6, color="#1E2761", label="Stayed")
    ax.plot(range(1, 7), left.values,   marker="o", lw=2.6, color="#C0392B", label="Left")
    ax.set_xlabel("Month  (1 = oldest, 6 = most recent)", fontsize=11)
    ax.set_ylabel("Average purchases", fontsize=11)
    ax.legend(frameon=False, fontsize=11)
    ax.grid(axis="y", color="#DDE3EE", lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#B9C4D6"); ax.spines["bottom"].set_color("#B9C4D6")
    ax.tick_params(colors="#5B6B7F", labelsize=10)
    fig.tight_layout()
    return fig

fig = plot_monthly_trend(df)
fig.savefig("/tmp/deck/trend.png", dpi=200, facecolor="white")
print("saved")
