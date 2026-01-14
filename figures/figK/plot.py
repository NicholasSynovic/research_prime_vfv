# ImageMagick Issue Density
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec
from numpy import ndarray
from pandas import DataFrame, Series, Timestamp
from pandas.core.groupby import DataFrameGroupBy, Grouper
from progress.bar import Bar
from sqlalchemy import Engine, create_engine

TS_WEEK_OFFSET: int = 20
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
        if ts > Timestamp.now():
            break

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
        "kloc_rate": [],
    }

    start_ts: Timestamp = Timestamp(ts_input=start_ts_str)
    end_ts: Timestamp = Timestamp(ts_input=end_ts_str)

    start_ts_offset: Timestamp = start_ts - pandas.Timedelta(weeks=TS_WEEK_OFFSET)
    end_ts_offset: Timestamp = end_ts + pandas.Timedelta(weeks=TS_WEEK_OFFSET)

    # Mask for date range
    mask = (df["date"] >= start_ts_offset) & (df["date"] <= end_ts_offset)
    masked_df: DataFrame = df.loc[mask]

    # Group by week
    dfgb = masked_df.groupby(by=Grouper(key="date", freq="W"))

    for ts, df_group in dfgb:
        if ts < start_ts_offset or ts > end_ts_offset:
            continue

        latest_df = df_group.tail(n=1)
        kloc = latest_df["code"].item() / 1000
        value = latest_df["open_events"].item() / kloc

        data["date"].append(ts)
        data["value"].append(value)
        data["kloc_rate"].append(kloc)  # temporarily store code as placeholder

    # Build DataFrame
    result_df = DataFrame(data=data).sort_values(by="date", ignore_index=True)

    # Compute week-to-week derivative of 'code' (stored in kloc_rate for now)
    if len(result_df) > 1:
        # compute difference in code (KLOC) divided by time (weeks)
        code_diff = np.gradient(result_df["kloc_rate"])
        time_deltas = result_df["date"].diff().dt.total_seconds() / (
            60 * 60 * 24 * 7
        )  # weeks
        time_deltas.iloc[0] = 1  # avoid NaN for first entry
        result_df["kloc_rate"] = code_diff / time_deltas
    else:
        result_df["kloc_rate"] = 0.0

    return result_df


def _subplot(
    ax: Axes,
    df: DataFrame,
    title: str,
    hide_xaxis: bool = False,
    hide_yaxis: bool = False,
    _rotate: bool = False,
    show_legend: bool = False,
    _shift_labels: bool = False,  # <--- NEW ARGUMENT
) -> None:
    # Modfies ax in place
    sns.barplot(data=df, x=df.index, y="value", ax=ax, color="steelblue")
    ax.set_title(title)
    ax.set_xlabel(xlabel="Week")
    ax.set_ylabel(ylabel="Issue Density")

    vuln_start: int = COMPUTE_WEEK_0_INDEX(df=df)
    vuln_end: int = COMPUTE_WEEK_N_INDEX(df=df)
    end_of_range: float = COMPUTE_RANGE_END(df=df)

    highlight_ranges: list[tuple[float, float, str, str]] = [
        (-0.5, vuln_start, "yellow", "Prior To Reintroduction."),
        (vuln_start, vuln_end, "lightcoral", "Post Reintroduction."),
        (vuln_end, end_of_range, "seagreen", "Post Correction"),
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
    if show_legend:
        ax.legend(
            handles=handles,
            loc="lower right",
            fontsize=8,  # smaller text
            frameon=True,  # show frame
            framealpha=1,  # slightly transparent
            handlelength=1.0,  # shorten line handles
            handletextpad=0.3,  # reduce space between line and text
            borderaxespad=0.2,  # reduce padding between axes and legend
            fancybox=True,  # rounded box
            borderpad=0.2,  # padding inside box
        )

    # Get the list of x-axis labels
    labels: list[str] = []
    tick_counter: int = 0
    # Collect the tick objects for later manipulation
    tick_objects = ax.get_xticklabels()
    for _ in tick_objects:
        labels.append(str(tick_counter))
        tick_counter += 1

    # If there are labels, set specific label indicies to be the dates for the
    # range start, introduction of the vulnerability, and the fix
    if labels:
        labels[0] = f"{df['date'].iloc[0].strftime(format='%m-%d-%y')}"
        labels[vuln_start] = (
            f"{df['date'].iloc[vuln_start].strftime(format='%m-%d-%y')}"
        )
        labels[vuln_end] = f"{df['date'].iloc[vuln_end].strftime(format='%m-%d-%y')}"
        labels[-1] = f"{df['date'].iloc[-1].strftime('%m-%d-%y')}"

    # Apply all labels at once
    ax.set_xticklabels(labels)

    # Iterate through the updated tick objects for formatting
    for idx, tick in enumerate(ax.get_xticklabels()):
        try:
            int(tick.get_text())
            tick.set_visible(b=False)
        except ValueError:
            tick.set_visible(b=True)
            if _rotate:
                # Retain rotation option, although not used in final fix
                tick.set_rotation(s=20)
                tick.set_horizontalalignment(align="right")
                tick.set_y(-0.01)

            # --- KEY CHANGE: Selective horizontal shift to prevent overlap
            if _shift_labels:
                # Shift the start date slightly to the left
                if idx == vuln_start:
                    # '0.2' is an arbitrary value that likely clears the overlap
                    x_shift = tick.get_position()[0] - 0.2
                    tick.set_x(x_shift)
                    # Align to the right for a clean look
                    tick.set_horizontalalignment("right")
                # Shift the end date slightly to the right
                elif idx == vuln_end:
                    x_shift = tick.get_position()[0] + 0.2
                    tick.set_x(x_shift)
                    # Align to the left for a clean look
                    tick.set_horizontalalignment("left")

    if hide_xaxis:
        ax.set_xlabel(xlabel="")

    if hide_yaxis:
        ax.set_ylabel(ylabel="")


def plot(
    df1: DataFrame,
    df2: DataFrame,
    df3: DataFrame,
    df4: DataFrame,
    df5: DataFrame,
) -> None:
    print(df1.iloc[-1])

    # Create the figure
    fig = plt.figure(figsize=(10, 6))
    gs = GridSpec(3, 2, figure=fig, hspace=0.55)  # Top is taller

    # --- Top wide plot (spans both columns)
    ax1 = fig.add_subplot(gs[0, :])
    sns.lineplot(data=df1, x="date", y="value", ax=ax1, color="steelblue")
    ax1.fill_between(df1["date"], df1["value"], color="skyblue", alpha=0.3)
    ax1.set_title("ImageMagick Issue Density")
    ax1.set_xlabel(xlabel="Year")
    ax1.set_ylabel(ylabel="Issue Density")
    ax1.set
    # --- Middle left plot
    ax2 = fig.add_subplot(gs[1, 0])
    _subplot(
        ax=ax2,
        df=df2,
        title="CVE-2016-4564",
        hide_xaxis=True,
        _shift_labels=True,  # <--- Enable label shifting here
    )

    # --- Middle right plot
    ax3 = fig.add_subplot(gs[1, 1])
    _subplot(ax=ax3, df=df3, title="CVE-2017-16546", hide_xaxis=True, hide_yaxis=True)

    # --- Bottom left plot
    ax4 = fig.add_subplot(gs[2, 0])
    _subplot(ax=ax4, df=df4, title="CVE-2018-11625")

    # --- Bottom right plot
    ax5 = fig.add_subplot(gs[2, 1])
    _subplot(ax=ax5, df=df5, title="CVE-2019-13299", hide_yaxis=True, show_legend=True)

    # Adjust layout and spacing and write the figure to disk
    plt.tight_layout()
    plt.savefig(f"figK.pdf", bbox_inches="tight", pad_inches=0)
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
        start_ts_str="11-04-2017",
        end_ts_str="03-14-2018",
    )  # CVE-2017-16546, 8.8 CVSS
    cve_3_metric: DataFrame = compute_cve(
        df=id_df,
        start_ts_str="05-30-2018",
        end_ts_str="04-08-2019",
    )  # CVE-2018-11625, CVSS 8.8
    cve_4_metric: DataFrame = compute_cve(
        df=id_df,
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
