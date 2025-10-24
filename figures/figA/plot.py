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


def create_commit_pairs_with_timestamps(
    csv_df: DataFrame,
    commits_df: DataFrame,
) -> DataFrame:
    # Get vulnerable commit pairs
    commits_1: Series = csv_df["commit_1"]
    commits_2: Series = csv_df["commit_2"]

    # Join the unique set of vulnerable commits
    commits: ndarray = pandas.concat(
        objs=[commits_1, commits_2],
        ignore_index=True,
    ).unique()

    # Select only commits from the `commits_df` from the set of unique commits
    commits_with_timestamps: DataFrame = commits_df.copy()
    commits_with_timestamps = commits_with_timestamps[
        commits_with_timestamps["commit_hash"].isin(commits)
    ]

    # Create a new DataFrame of commit pairs with timestamps
    data: dict[str, list[str | Timestamp]] = {
        "commit_1": [],
        "commit_2": [],
        "commit_1_timestamp": [],
        "commit_2_timestamp": [],
    }

    row: Series
    for _, row in csv_df.iterrows():
        data["commit_1"].append(row["commit_1"])
        data["commit_2"].append(row["commit_2"])

        # Based on the commit_1 or commit_2 value, get the committed_datetime
        # value in the commits_with_timestamps DataFrame by indexing into the
        # column.
        data["commit_1_timestamp"].append(
            commits_with_timestamps[
                commits_with_timestamps["commit_hash"] == row["commit_1"]
            ]["committed_datetime"].reset_index(drop=True)[0],
        )
        data["commit_2_timestamp"].append(
            commits_with_timestamps[
                commits_with_timestamps["commit_hash"] == row["commit_2"]
            ]["committed_datetime"].reset_index(drop=True)[0],
        )

    return DataFrame(data=data)


def compute(
    commit_pairs: DataFrame,
    df: DataFrame,
    timestamp_week_offset: int = 3,
) -> list[tuple[int, Timestamp, Timestamp, DataFrame]]:
    # Create variable to store a list of tuple pairings with index 0 is the
    # commit pair row index (that maps to the CSV file row), index 1 is the
    # start date of the vulnerability, index 2 is the end date of the
    # vulnerability, and index 3 is the computed DataFrame used for plotting.
    # NOTE: The start and end dates are not the min and max values of the
    # DataFrame due to offsetting the dates for better presentation
    data: list[tuple[int, Timestamp, Timestamp, DataFrame]] = []

    with Bar("Computing data...", max=commit_pairs.shape[0]) as bar:
        # For each commit pair, compute the metric
        commit_pair_row: Series
        idx: int
        for idx, commit_pair_row in commit_pairs.iterrows():
            # Copy empty dictionary to manipulate
            datum: dict[str, list[Timestamp | int]] = {"date": [], "value": []}

            # Make a copy of the `df` DataFrame
            df = df.copy()

            # Get start and end timestamp
            start_ts: Timestamp = commit_pair_row["commit_1_timestamp"]
            end_ts: Timestamp = commit_pair_row["commit_2_timestamp"]

            # Offset the start and end days
            start_ts_offset: Timestamp = start_ts - pandas.Timedelta(
                weeks=timestamp_week_offset
            )
            end_ts_offset: Timestamp = end_ts + pandas.Timedelta(
                weeks=timestamp_week_offset
            )

            # Create a mask on the range of dates that we are interested in
            mask = (df["date"] >= start_ts_offset) & (df["date"] <= end_ts_offset)
            masked_df: DataFrame = df.loc[mask]

            # Create groups of DataFrames by weekly date from `masked_df`
            dfgb: DataFrameGroupBy = masked_df.groupby(
                by=Grouper(key="date", freq="W"),
            )

            # For each DataFrame group, compute the metric if the date range is
            # between the start and end Timestamps
            df_group: DataFrame
            ts: Timestamp
            for ts, df_group in dfgb:
                if ts < start_ts_offset:
                    continue
                if ts > end_ts_offset:
                    break

                # Compute metric
                value: int = df_group["committer_id"].unique().size

                # Write data to dictionary
                datum["date"].append(ts)
                datum["value"].append(value)

            # Create tuple[int, DataFrame] and append to the list
            data.append(
                (
                    idx,
                    start_ts,
                    end_ts,
                    DataFrame(data=datum).sort_values(
                        by="date",
                        ignore_index=True,
                    ),
                )
            )

            bar.next()

    return data


def plot(
    pair_id: int,
    start_ts: Timestamp,
    end_ts: Timestamp,
    df: DataFrame,
    ts_offset: int = 3,
) -> None:
    # Ranges to plot highlight boxes. Compute the `yellow_highlight_end` by
    # subtracting the offset from the number of rows in the `df`.
    yellow_highlight_end: int = df.shape[0] - ts_offset
    highlight_ranges: list[tuple[float, float, str, str]] = [
        (-0.5, ts_offset, "red", "Prior To Risky Fix"),
        (ts_offset, yellow_highlight_end, "yellow", "Post Risky Fix"),
        (
            yellow_highlight_end,
            yellow_highlight_end + ts_offset + 0.5,
            "green",
            "Post Corrective Fix",
        ),
    ]

    # Legned handles
    handles: list = []

    # Plot bar chart
    fig, ax = plt.subplots()
    sns.barplot(data=df, x="date", y="value", ax=ax)

    # Store patches into the `handles` variable
    start: float
    end: float
    color: str
    for start, end, color, patch_label in highlight_ranges:
        patch = ax.axvspan(
            start,
            end,
            color=color,
            alpha=0.75,
            zorder=0,
            label=patch_label,
        )
        handles.append(patch)

    # Plot the legend
    ax.legend(handles=handles, loc="lower right", framealpha=1, frameon=True)

    # Get the list of x-axis labels
    labels: list[str] = []
    tick_counter: int = 0
    for tick in ax.get_xticklabels():
        labels.append(str(tick_counter))
        tick_counter += 1

    # If there are labels, set specific label indicies to be the dates for the
    # range start, introduction of the vulnerability, and the fix
    # TODO: Make sure that the labels align with the proper dates
    if labels:
        labels[0] = (
            f"{(start_ts - pandas.Timedelta(weeks=ts_offset)).strftime(format='%m-%d-%y')}"
        )
        labels[3] = f"{start_ts.strftime(format='%m-%d-%y')}"
        labels[yellow_highlight_end] = f"{end_ts.strftime(format='%m-%d-%y')}"
        ax.set_xticklabels(labels, rotation=45, ha="right")

    # Set titles and x and y axis labels
    ax.set_title(f"Time To Fix: {(end_ts - start_ts).days} Days", fontsize=10)
    fig.suptitle("ImageMagick Bus Factor per Week", fontsize=12)
    ax.set_xlabel("Week")
    ax.set_ylabel("Bus Factor")

    # Write the figure to disk
    plt.tight_layout()
    plt.savefig(f"figA_metric{pair_id}.pdf")
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
@click.option(
    "-c",
    "--csv-path",
    type=lambda x: Path(x).resolve(),
    help="Path to ImageMagick commit pairs",
    required=True,
)
def main(db_path: Path, csv_path: Path) -> None:
    # Read data from the CSV file
    csv_df: DataFrame = read_csv(fp=csv_path)

    # Read data from the database
    db_engine: Engine = create_engine(url=f"sqlite:///{db_path}")
    bf_df: DataFrame = read_bus_factor_from_db(db_engine=db_engine)
    commits_df: DataFrame = read_commit_logs_from_db(db_engine=db_engine)

    # Select commits from the `commits_df` DataFrame if and only if they exist
    # in the `csv_df` DataFrame
    commit_pairs: DataFrame = create_commit_pairs_with_timestamps(
        csv_df=csv_df,
        commits_df=commits_df,
    )

    # Compute metric
    metric_values: list[tuple[int, Timestamp, Timestamp, DataFrame]] = compute(
        commit_pairs=commit_pairs,
        df=bf_df,
    )

    # Plot per metric
    value: tuple[int, Timestamp, Timestamp, DataFrame]
    for value in metric_values:
        plot(pair_id=value[0], start_ts=value[1], end_ts=value[2], df=value[3])


if __name__ == "__main__":
    main()
