import json
from os import listdir
from pathlib import Path

import click
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import DataFrame
from progress.bar import Bar


def load_data(dir: Path) -> DataFrame:
    # Data structure to store DataFrames
    data: list[dict[str, list[str | float]]] = []

    # Paths to JSON files
    json_files: list[Path] = [Path(dir, fp).resolve() for fp in dir.iterdir()]

    with Bar("Reading JSON files into Pandas DataFrame...", max=len(json_files)) as bar:
        jf: Path
        for jf in json_files:
            record: dict[str, list[str | float]] = {}

            # Read JSON data
            json_data: dict = json.load(fp=jf.open(mode="r"))

            # Get top-level project details
            record["repo"] = json_data["repo"]["name"].replace("github.com/", "")
            record["score"] = json_data["score"]

            # Get individual checks
            check: dict
            for check in json_data["checks"]:
                record[check["name"]] = check["score"]

            data.append(record)
            bar.next()

    return DataFrame(data=data)


def plot(df: DataFrame) -> None:
    sns.heatmap(data=df, antialiased=True)

    plt.title("OpenSSF Check Scores Of Top 10 Repositories")
    plt.xlabel(xlabel="OpenSSF Check")
    plt.ylabel(ylabel="Github Hosted Repository")
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig("figE.pdf")


@click.command()
@click.option(
    "-i",
    "--input-dir",
    required=True,
    type=lambda x: Path(x).resolve(),
    help="Path to OpenSSF Scorecard JSON files",
)
def main(input_dir: Path) -> None:
    # Create DataFrame
    df: DataFrame = load_data(dir=input_dir)

    # Sort DataFrame on score and only keep the top ten highest ranking
    df = df.sort_values(by="score", ascending=False, ignore_index=True)[0:10]

    # Drop the score column
    df = df.drop(columns="score")

    # Set the index to be the repo
    df = df.set_index(keys="repo")

    # Plot the heatmap
    plot(df=df)


if __name__ == "__main__":
    main()
