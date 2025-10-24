from pathlib import Path

import click
import matplotlib.pyplot as plt
import pandas
import seaborn as sns
from pandas import DataFrame, Timestamp
from pandas.core.groupby import DataFrameGroupBy, Grouper
from sqlalchemy import Engine, create_engine

COMMIT_1: Timestamp = Timestamp(ts_input="02-02-2016")
COMMIT_2: Timestamp = Timestamp(ts_input="06-02-2016")

STARTING_DATE: Timestamp = (
    Timestamp(ts_input="02-02-2016") - pandas.Timedelta(weeks=3)
).floor("D")
ENDING_DATE: Timestamp = (
    Timestamp(ts_input="06-02-2016") + pandas.Timedelta(weeks=3)
).floor("D")


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | int]] = {"date": [], "pr_spoilage": []}

    dfgb: DataFrameGroupBy = df.groupby(by=Grouper(key="timestamp", freq="W"))

    count: int = 0
    _df: DataFrame
    ts: Timestamp
    for ts, _df in dfgb:
        if ts < STARTING_DATE:
            continue
        if ts > ENDING_DATE:
            break

        issue_spoilage: int = _df["pr_spoilage"].sum()

        data["date"].append(count)
        data["pr_spoilage"].append(issue_spoilage)

        count += 1

    return DataFrame(data=data)


def plot(df: DataFrame) -> None:
    # sns.barplot(data=df, x="date", y="bf")

    # plt.suptitle(t="ImageMagick Bus Factor per Week")
    # plt.title(label="Time To Fix: 120 Days")
    # plt.xlabel(xlabel="Week")
    # plt.ylabel(ylabel="Bus Factor")
    # plt.tight_layout()

    # plt.savefig("figA.pdf")
    fig, ax = plt.subplots()

    # --- BARPLOT ---
    sns.barplot(data=df, x="date", y="pr_spoilage", ax=ax)

    # --- COLORED BOXES ---
    # Example: highlight specific time ranges (adjust indices or date values as needed)
    highlight_ranges = [
        (-0.5, 3, "red", "Prior To Risky Fix"),  # weeks 2–5
        (3, 17, "yellow", "Post Risky Fix"),  # weeks 10–12
        (17, 22.5, "green", "Post Corrective Fix"),
    ]
    # Store handles for legend
    handles = []
    labels = []

    for start, end, color, label in highlight_ranges:
        patch = ax.axvspan(start, end, color=color, alpha=0.75, zorder=0, label=label)
        handles.append(patch)
        labels.append(label)

    # --- LEGEND ---
    ax.legend(handles=handles, loc="lower right", framealpha=1, frameon=True)

    # --- CUSTOM X-TICK LABELS ---
    # Get tick positions and labels from the plot
    ticks = ax.get_xticks()
    labels = [tick.get_text() for tick in ax.get_xticklabels()]

    # Make sure there are labels before modifying
    if labels:
        labels[0] = f"{STARTING_DATE.strftime(format='%m-%d-%y')}"
        labels[3] = f"{COMMIT_1.strftime(format='%m-%d-%y')}"
        labels[17] = f"{ENDING_DATE.strftime(format='%m-%d-%y')}"
        ax.set_xticklabels(labels, rotation=45, ha="right")

    # --- TITLES & LABELS ---
    ax.set_title("Time To Fix: 120 Days", fontsize=10)
    fig.suptitle("ImageMagick Pull Request Spoilage per Week", fontsize=12)
    ax.set_xlabel("Week")
    ax.set_ylabel("Pull Request Spoilage")

    plt.tight_layout()
    plt.savefig("figI.pdf")


def main() -> None:
    df: DataFrame = pandas.read_csv(filepath_or_buffer="pr_spoilage.csv")
    df["timestamp"] = df["timestamp"].apply(func=Timestamp)

    bf_df: DataFrame = compute(df=df)

    print(bf_df)

    plot(df=bf_df)


if __name__ == "__main__":
    main()
