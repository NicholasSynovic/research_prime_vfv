# ImageMagick Issue Spoilage
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


def compute(df: DataFrame) -> DataFrame:
    data: dict[str, list[Timestamp | int]] = {"date": [], "value": []}

    dfgb: DataFrameGroupBy = df.groupby(by=Grouper(key="date", freq="6ME"))

    _df: DataFrame
    ts: Timestamp
    for ts, _df in dfgb:
        if ts > Timestamp.now():
            break

        value: int = _df["issue_spoilage"].tail(n=1).item()

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

        value: int = df_group["issue_spoilage"].tail(n=1).item()

        # Write data to dictionary
        data["date"].append(ts)
        data["value"].append(value)

    return DataFrame(data=data)


def _subplot(ax, df: DataFrame, title: str) -> None:
    # Modfies ax in place
    sns.barplot(data=df, x=df.index, y="value", ax=ax, color="steelblue")
    ax.set_title(title)
    ax.set_xlabel(xlabel="Week")
    ax.set_ylabel(ylabel="Issue Spoilage")

    vuln_start: int = COMPUTE_WEEK_0_INDEX(df=df)
    vuln_end: int = COMPUTE_WEEK_N_INDEX(df=df)
    end_of_range: float = COMPUTE_RANGE_END(df=df)

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
    for _ in ax.get_xticklabels():
        labels.append(str(tick_counter))
        tick_counter += 1

    # If there are labels, set specific label indicies to be the dates for the
    # range start, introduction of the vulnerability, and the fix
    # TODO: Make sure that the labels align with the proper dates
    if labels:
        labels[0] = f"{df['date'].iloc[0].strftime(format='%m-%d-%y')}"
        labels[vuln_start] = (
            f"{df['date'].iloc[vuln_start].strftime(format='%m-%d-%y')}"
        )
        labels[vuln_end] = f"{df['date'].iloc[vuln_end].strftime(format='%m-%d-%y')}"

    # Rotate ticks that are dates
    ax.set_xticklabels(labels)
    for tick in ax.get_xticklabels():
        try:
            int(tick.get_text())
            tick.set_visible(b=False)
        except ValueError:
            tick.set_visible(b=True)
            tick.set_rotation(s=45)
            tick.set_horizontalalignment(align="right")


def plot(
    df1: DataFrame,
    df2: DataFrame,
    df3: DataFrame,
    df4: DataFrame,
    df5: DataFrame,
) -> None:
    # Create the figure
    fig = plt.figure(figsize=(10, 6))
    gs = GridSpec(2, 4, height_ratios=[1, 2], figure=fig)  # Top is taller

    # --- Top wide plot (spans both columns)
    ax1 = fig.add_subplot(gs[0, :])
    sns.lineplot(data=df1, x="date", y="value", ax=ax1, color="steelblue")
    ax1.fill_between(df1["date"], df1["value"], color="skyblue", alpha=0.3)
    ax1.set_title("ImageMagick Issue Spoilage")
    ax1.set_xlabel(xlabel="Year")
    ax1.set_ylabel(ylabel="Issue Spoilage")

    # --- Bottom left plot
    ax2 = fig.add_subplot(gs[1, 0])
    _subplot(ax=ax2, df=df2, title="CVE-2016-4564")

    # --- Bottom center left plot
    ax3 = fig.add_subplot(gs[1, 1])
    _subplot(ax=ax3, df=df3, title="CVE-2017-16546")

    # --- Bottom center left plot
    ax4 = fig.add_subplot(gs[1, 2])
    _subplot(ax=ax4, df=df4, title="CVE-2018-11625")

    # --- Bottom center left plot
    ax5 = fig.add_subplot(gs[1, 3])
    _subplot(ax=ax5, df=df5, title="CVE-2019-13299")

    # Adjust layout and spacing and write the figure to disk
    plt.tight_layout()
    plt.savefig(f"figM.pdf")
    plt.clf()
    plt.close()


def main() -> None:
    is_df: DataFrame = pandas.read_csv(filepath_or_buffer="issue_spoilage.csv")
    is_df["timestamp"] = is_df["timestamp"].apply(func=Timestamp)
    is_df = is_df.rename(columns={"timestamp": "date"})

    project_metric: DataFrame = compute(df=is_df)
    cve_1_metric: DataFrame = compute_cve(
        df=is_df,
        start_ts_str="05-04-2016",
        end_ts_str="06-11-2016",
    )  # CVE-2016-4564, 9.8 CVSS
    cve_2_metric: DataFrame = compute_cve(
        df=is_df,
        start_ts_str="11-04-2017",
        end_ts_str="03-14-2018",
    )  # CVE-2017-16546, 8.8 CVSS
    cve_3_metric: DataFrame = compute_cve(
        df=is_df,
        start_ts_str="05-30-2018",
        end_ts_str="04-08-2019",
    )  # CVE-2018-11625, CVSS 8.8
    cve_4_metric: DataFrame = compute_cve(
        df=is_df,
        start_ts_str="06-23-2019",
        end_ts_str="01-10-2020",
    )  # CVE-2019-13299, 8.8 CVSS

    # Plot per metric
    plot(
        df1=project_metric,
        df2=cve_1_metric,
        df3=cve_2_metric,
        df4=cve_3_metric,
        df5=cve_4_metric,
    )


if __name__ == "__main__":
    main()
