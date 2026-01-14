# ImageMagick Bus Factor
from pathlib import Path

import click
import matplotlib.pyplot as plt
import pandas
import seaborn as sns
from matplotlib.gridspec import GridSpec
from numpy import ndarray
from pandas import DataFrame, Series, Timestamp
from pandas.core.groupby import DataFrameGroupBy, Grouper
from progress.bar import Bar
from sqlalchemy import Engine, create_engine


def read_bus_factor_from_db(db_engine: Engine) -> DataFrame:
    df: DataFrame = pandas.read_sql_table(
        table_name="bus_factor_per_day",
        con=db_engine,
        index_col="id",
    )

    df["date"] = df["date"].apply(func=Timestamp)
    return df


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | int]] = {"date": [], "value": []}

    # Create groups of DataFrames by weekly date from `masked_df`
    dfgb: DataFrameGroupBy = df.groupby(
        by=Grouper(key="date", freq="6ME"),
    )

    # For each DataFrame group, compute the metric if the date range is
    # between the start and end Timestamps
    df_group: DataFrame
    ts: Timestamp
    for ts, df_group in dfgb:
        if ts > Timestamp.now():
            break

        # Compute metric
        value: int = df_group["committer_id"].unique().size

        # Write data to dictionary
        data["date"].append(ts)
        data["value"].append(value)

    return DataFrame(data=data)


def plot(df: DataFrame) -> None:
    # Create the figure
    fig = plt.figure(figsize=(10, 3))
    gs = GridSpec(1, 1, figure=fig)  # Top is taller

    # --- Top wide plot (spans both columns)
    ax1 = fig.add_subplot(gs[0, :])
    sns.lineplot(data=df, x="date", y="value", ax=ax1, color="steelblue")
    ax1.fill_between(df["date"], df["value"], color="skyblue", alpha=0.3)
    ax1.set_title("ImageMagick Bus Factor", fontsize=16)
    ax1.set_xlabel(xlabel="Year", fontsize=14)
    ax1.set_ylabel(ylabel="Bus Factor", fontsize=14)
    ax1.set_ylim(bottom=0, top=8)

    plt.tick_params(axis="both", labelsize=12)
    plt.tight_layout()
    plt.savefig("figN.pdf")


@click.command()
@click.option(
    "-d",
    "--db-path",
    type=lambda x: Path(x).resolve(),
    help="Path to PRIME database",
    required=True,
)
def main(db_path: Path) -> None:
    # Read data from the database
    db_engine: Engine = create_engine(url=f"sqlite:///{db_path}")
    bf_df: DataFrame = read_bus_factor_from_db(db_engine=db_engine)

    # Compute metric
    df: DataFrame = compute(df=bf_df)

    # Plot per metric
    plot(df=df)


if __name__ == "__main__":
    main()
