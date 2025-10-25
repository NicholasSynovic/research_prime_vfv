from pathlib import Path

import click
import matplotlib.pyplot as plt
import pandas
import seaborn as sns
from numpy import ndarray
from pandas import DataFrame, Series, Timestamp
from pandas.core.groupby import DataFrameGroupBy, Grouper
from progress.bar import Bar
from sqlalchemy import Engine, create_engine


def read_csv(fp: Path, sep: str = "|") -> DataFrame:
    df: DataFrame = pandas.read_csv(filepath_or_buffer=fp, sep=sep)
    return df.rename(
        columns={"commit": "commit_1", "future_commit_id": "commit_2"},
    )


def read_bus_factor_from_db(db_engine: Engine) -> DataFrame:
    df: DataFrame = pandas.read_sql_table(
        table_name="bus_factor_per_day",
        con=db_engine,
        index_col="id",
    )

    df["date"] = df["date"].apply(func=Timestamp)
    return df


def read_commit_logs_from_db(db_engine: Engine) -> DataFrame:
    sql_query: str = """
    SELECT
        commit_logs.id, commit_hashes.commit_hash, commit_logs.committed_datetime
    FROM
        commit_logs
    JOIN
        commit_hashes
    ON
        commit_logs.commit_hash_id = commit_hashes.id;
    """

    df: DataFrame = pandas.read_sql(
        sql=sql_query,
        con=db_engine,
        index_col="id",
    )

    df["committed_datetime"] = df["committed_datetime"].apply(func=Timestamp)
    return df


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | int]] = {
        "date": [],
        "value": [],
    }

    with Bar("Computing data...", max=df.shape[0]) as bar:
        dfgb: DataFrameGroupBy = df.groupby(
            by=Grouper(key="date", freq="6ME"),
        )

        # For each DataFrame group, compute the metric if the date range is
        # between the start and end Timestamps
        df_group: DataFrame
        for ts, df_group in dfgb:
            # Compute metric
            value: int = df_group["committer_id"].unique().size

            # Write data to dictionary
            data["date"].append(ts)
            data["value"].append(value)

            bar.next()

    return DataFrame(data=data)


def plot(
    df: DataFrame,
) -> None:
    # Ranges to plot highlight boxes. Compute the `yellow_highlight_end` by
    # subtracting the offset from the number of rows in the `df`.
    sns.barplot(data=df, x="date", y="value")

    plt.suptitle(t="ImageMagick Bus Factor")
    plt.title(label="Measurements Taken Every 6 Months")
    plt.xlabel(xlabel="Date")
    plt.ylabel(ylabel="Bus Factor")

    # Write the figure to disk
    plt.tight_layout()
    plt.savefig(f"figJ.pdf")
    plt.clf()
    plt.close()


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
    metric_values: DataFrame = compute(df=bf_df)

    plot(df=metric_values)

    # Plot per metric
    # value: tuple[int, Timestamp, Timestamp, DataFrame]
    # for value in metric_values:
    #     plot(pair_id=value[0], start_ts=value[1], end_ts=value[2], df=value[3])


if __name__ == "__main__":
    main()
