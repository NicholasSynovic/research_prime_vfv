# ImageMagick Issue Density
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

TS_WEEK_OFFSET: int = 3
COMPUTE_WEEK_0_INDEX = lambda df: df[
    df["date"]
    == df["date"].iloc[0]
    + pandas.Timedelta(
        weeks=TS_WEEK_OFFSET,
    )
].index[0]
COMPUTE_WEEK_N_INDEX = lambda df: df[
    df["date"]
    == df["date"].iloc[-1]
    - pandas.Timedelta(
        weeks=TS_WEEK_OFFSET,
    )
].index[0]
COMPUTE_RANGE_END = lambda df: df["date"].index[-1] + 0.5


def read_issue_desnity_from_db(db_engine: Engine) -> DataFrame:
    df: DataFrame = pandas.read_sql_table(
        table_name="issue_density_per_day",
        con=db_engine,
        index_col="id",
    )

    df["start"] = df["start"].apply(func=Timestamp)
    df = df.rename(columns={"start": "date"})

    return df[["date", "open_events", "code"]]


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | float]] = {
        "date": [],
        "value": [],
    }

    dfgb: DataFrameGroupBy = df.groupby(
        by=Grouper(key="date", freq="6ME"),
    )

    df_group: DataFrame
    ts: Timestamp
    for ts, df_group in dfgb:
        latest_df: DataFrame = df_group.tail(n=1)
        kloc: float = latest_df["code"].item() / 1000
        value: float = latest_df["open_events"].item() / kloc

        # Write data to dictionary
        data["date"].append(ts)
        data["value"].append(value)

    return DataFrame(data=data)


def compute_cve(
    df: DataFrame,
    start_ts_str: str,
    end_ts_str: str,
) -> DataFrame:
    data: dict[str, list[Timestamp | float]] = {
        "date": [],
        "value": [],
    }

    start_ts: Timestamp = Timestamp(ts_input=start_ts_str)
    end_ts: Timestamp = Timestamp(ts_input=end_ts_str)

    start_ts_offset: Timestamp = start_ts - pandas.Timedelta(
        weeks=TS_WEEK_OFFSET,
    )
    end_ts_offset: Timestamp = end_ts + pandas.Timedelta(weeks=TS_WEEK_OFFSET)

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

        latest_df: DataFrame = df_group.tail(n=1)
        kloc: float = latest_df["code"].item() / 1000
        value: float = latest_df["open_events"].item() / kloc

        # Write data to dictionary
        data["date"].append(ts)
        data["value"].append(value)

    return DataFrame(data=data)


# def plot(df: DataFrame) -> None:
#     sns.barplot(data=df, x="date", y="value")

#     plt.suptitle(t="ImageMagick Issue Density")
#     plt.title(label="Measurements Taken Every 6 Months")
#     plt.xlabel(xlabel="Date")
#     plt.ylabel(ylabel="Issue Density")

#     # Write the figure to disk
#     plt.tight_layout()
#     plt.savefig(f"figK.pdf")
#     plt.clf()
#     plt.close()


def plot(df1: DataFrame, df2: DataFrame, df3: DataFrame) -> None:
    # Create the figure
    fig = plt.figure(figsize=(10, 6))
    gs = GridSpec(2, 2, height_ratios=[1, 2], figure=fig)  # Top is taller

    # --- Top wide plot (spans both columns)
    ax1 = fig.add_subplot(gs[0, :])
    sns.lineplot(data=df1, x="date", y="value", ax=ax1, color="steelblue")
    ax1.fill_between(df1["date"], df1["value"], color="skyblue", alpha=0.3)
    ax1.set_title("ImageMagick Issue Density")
    ax1.set_xlabel(xlabel="Year")
    ax1.set_ylabel(ylabel="Issue Density")

    # --- Bottom left plot

    ax2 = fig.add_subplot(gs[1, 0])
    sns.barplot(data=df2, x=df2.index, y="value", ax=ax2, color="steelblue")
    ax2.set_title("CVE-2016-4564 Issue Density")
    ax2.set_xlabel(xlabel="Week")
    ax2.set_ylabel(ylabel="Issue Density")

    vuln_start: int = COMPUTE_WEEK_0_INDEX(df=df2)
    vuln_end: int = COMPUTE_WEEK_N_INDEX(df=df2)
    end_of_range: float = COMPUTE_RANGE_END(df=df2)

    highlight_ranges: list[tuple[float, float, str, str]] = [
        (-0.5, vuln_start, "yellow", "Prior To Risky Fix"),
        (vuln_start, vuln_end, "lightcoral", "Post Risky Fix"),
        (vuln_end, end_of_range, "seagreen", "Post Corrective Fix"),
    ]

    # Store patches into the `handles` variable
    handles: list = []
    start: float
    end: float
    color: str
    for start, end, color, patch_label in highlight_ranges:
        patch = ax2.axvspan(
            start,
            end,
            color=color,
            alpha=0.75,
            zorder=0,
            label=patch_label,
        )
        handles.append(patch)

    # Plot the legend
    ax2.legend(handles=handles, loc="lower right", framealpha=1, frameon=True)

    # Get the list of x-axis labels
    labels: list[str] = []
    tick_counter: int = 0
    for _ in ax2.get_xticklabels():
        labels.append(str(tick_counter))
        tick_counter += 1

    # If there are labels, set specific label indicies to be the dates for the
    # range start, introduction of the vulnerability, and the fix
    # TODO: Make sure that the labels align with the proper dates
    if labels:
        labels[0] = f"{df2['date'].iloc[0].strftime(format='%m-%d-%y')}"
        labels[vuln_start] = (
            f"{df2['date'].iloc[vuln_start].strftime(format='%m-%d-%y')}"
        )
        labels[vuln_end] = f"{df2['date'].iloc[vuln_end].strftime(format='%m-%d-%y')}"

    # Rotate ticks that are dates
    ax2.set_xticklabels(labels)
    for tick in ax2.get_xticklabels():
        try:
            int(tick.get_text())
        except ValueError:
            tick.set_visible(b=True)
            tick.set_rotation(s=45)
            tick.set_horizontalalignment(align="right")

    # --- Bottom right plot
    ax3 = fig.add_subplot(gs[1, 1])
    sns.barplot(data=df3, x=df3.index, y="value", ax=ax3, color="steelblue")
    ax3.set_title("CVE-2019-13299 Issue Density")
    ax3.set_xlabel(xlabel="Week")
    ax3.set_ylabel(ylabel="Issue Density")

    vuln_start: int = COMPUTE_WEEK_0_INDEX(df=df3)
    vuln_end: int = COMPUTE_WEEK_N_INDEX(df=df3)
    end_of_range: float = COMPUTE_RANGE_END(df=df3)

    highlight_ranges: list[tuple[float, float, str, str]] = [
        (-0.5, vuln_start, "yellow", "Prior To Risky Fix"),
        (vuln_start, vuln_end, "lightcoral", "Post Risky Fix"),
        (vuln_end, end_of_range, "seagreen", "Post Corrective Fix"),
    ]

    # Store patches into the `handles` variable
    handles: list = []
    start: float
    end: float
    color: str
    for start, end, color, patch_label in highlight_ranges:
        patch = ax3.axvspan(
            start,
            end,
            color=color,
            alpha=0.75,
            zorder=0,
            label=patch_label,
        )
        handles.append(patch)

    # Plot the legend
    ax3.legend(handles=handles, loc="lower right", framealpha=1, frameon=True)

    # Get the list of x-axis labels
    labels: list[str] = []
    tick_counter: int = 0
    for _ in ax3.get_xticklabels():
        labels.append(str(tick_counter))
        tick_counter += 1

    # If there are labels, set specific label indicies to be the dates for the
    # range start, introduction of the vulnerability, and the fix
    # TODO: Make sure that the labels align with the proper dates
    if labels:
        labels[0] = f"{df3['date'].iloc[0].strftime(format='%m-%d-%y')}"
        labels[vuln_start] = (
            f"{df3['date'].iloc[vuln_start].strftime(format='%m-%d-%y')}"
        )
        labels[vuln_end] = f"{df3['date'].iloc[vuln_end].strftime(format='%m-%d-%y')}"

    # Rotate ticks that are dates
    ax3.set_xticklabels(labels)
    for tick in ax3.get_xticklabels():
        try:
            int(tick.get_text())
        except ValueError:
            tick.set_rotation(s=45)
            tick.set_horizontalalignment(align="right")
        else:
            tick_value: int = int(tick.get_text())
            if tick_value % 2 == 1:
                tick.set_visible(b=False)

            if vuln_start - tick_value > 0:
                tick.set_visible(b=False)

            if vuln_end - 1 == tick_value:
                tick.set_visible(b=False)

    # Adjust layout and spacing
    # Write the figure to disk
    plt.tight_layout()
    plt.savefig(f"figK.pdf")
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
    id_df: DataFrame = read_issue_desnity_from_db(db_engine=db_engine)

    project_metric: DataFrame = compute(df=id_df)
    cve_1_metric: DataFrame = compute_cve(
        df=id_df,
        start_ts_str="05-04-2016",
        end_ts_str="06-11-2016",
    )  # CVE-2016-4564, 9.8 CVSS
    cve_2_metric: DataFrame = compute_cve(
        df=id_df,
        start_ts_str="06-23-2019",
        end_ts_str="01-10-2020",
    )  # CVE-2019-13299, 8.8 CVSS

    # Plot per metric
    plot(df1=project_metric, df2=cve_1_metric, df3=cve_2_metric)


if __name__ == "__main__":
    main()
