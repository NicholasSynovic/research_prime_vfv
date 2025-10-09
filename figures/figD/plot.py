from pathlib import Path

import click
import matplotlib.pyplot as plt
import pandas
import seaborn as sns
from pandas import DataFrame, Timestamp
from pandas.core.groupby import DataFrameGroupBy, Grouper
from sqlalchemy import Engine, create_engine


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | int]] = {"date": [], "id": []}

    dfgb: DataFrameGroupBy = df.groupby(by=Grouper(key="start", freq="12ME"))

    count: int = 0
    _df: DataFrame
    for _, _df in dfgb:
        latest_df: DataFrame = _df.tail(n=1)

        data["date"].append(count)
        data["id"].append(latest_df["open_events"].item())

        count += 1

    return DataFrame(data=data)


def plot(df: DataFrame) -> None:
    sns.barplot(data=df, x="date", y="id")

    plt.title(label="ImageMagick Pull Request Spoilage per Year")
    plt.xlabel(xlabel="Year")
    plt.ylabel(ylabel="Pull Request Spoilage")
    plt.tight_layout()

    plt.savefig("figD.pdf")


@click.command()
@click.option(
    "-i",
    "--input-db",
    type=lambda x: Path(x).resolve(),
    help="Path to PRIME database",
    required=True,
)
def main(input_db: Path) -> None:
    db: Engine = create_engine(url=f"sqlite:///{input_db}")
    df: DataFrame = pandas.read_sql_table(
        table_name="pull_request_spoilage_per_day",
        con=db,
        index_col="id",
    )

    bf_df: DataFrame = compute(df=df)

    plot(df=bf_df)


if __name__ == "__main__":
    main()
