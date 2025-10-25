from pathlib import Path

import click
import matplotlib.pyplot as plt
import pandas
import seaborn as sns
from pandas import DataFrame, Timestamp
from pandas.core.groupby import DataFrameGroupBy, Grouper
from sqlalchemy import Engine, create_engine


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | int]] = {"date": [], "value": []}

    dfgb: DataFrameGroupBy = df.groupby(by=Grouper(key="timestamp", freq="6ME"))

    _df: DataFrame
    ts: Timestamp
    for ts, _df in dfgb:
        issue_spoilage: int = _df["issue_spoilage"].sum()

        data["date"].append(ts)
        data["value"].append(issue_spoilage)

    return DataFrame(data=data)


def plot(df: DataFrame) -> None:
    sns.barplot(data=df, x="date", y="value")

    plt.suptitle(t="ImageMagick Issue Spoilage")
    plt.title(label="Measurements Taken Every 6 Months")
    plt.xlabel(xlabel="Date")
    plt.ylabel(ylabel="Issue Spoilage (log Scale)")

    plt.yscale(value="log")

    # Write the figure to disk
    plt.tight_layout()
    plt.savefig(f"figM.pdf")
    plt.clf()
    plt.close()


def main() -> None:
    df: DataFrame = pandas.read_csv(filepath_or_buffer="issue_spoilage.csv")
    df["timestamp"] = df["timestamp"].apply(func=Timestamp)

    bf_df: DataFrame = compute(df=df)

    plot(df=bf_df)


if __name__ == "__main__":
    main()
