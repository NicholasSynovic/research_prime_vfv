from argparse import ArgumentParser, Namespace
from pathlib import Path

import pandas
from pandas import DataFrame

PROGRAM_NAME: str = "Repository Extractor"


def cli() -> Namespace:
    # Command line argument parser
    parser: ArgumentParser = ArgumentParser(prog=PROGRAM_NAME)

    # Get input file path
    parser.add_argument(
        "-i",
        "--input",
        type=lambda x: Path(x).resolve(),
        required=True,
        help="Path to input CSV file",
    )

    # Get output file path
    parser.add_argument(
        "-o",
        "--output",
        type=lambda x: Path(x).resolve(),
        required=True,
        help="Path to output JSON file",
    )

    # Parse args
    return parser.parse_args()


def parse_data(df: DataFrame) -> DataFrame:
    # Get relevant columns
    df = df[["Project", "codeLink", "CWE ID", "CVE ID"]]

    # Modify column names
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(pat=" ", repl="_")
    df = df.rename(columns={"codelink": "url"})

    # Convert commit URLs to GitHub urls
    df["url"] = df["url"].apply(lambda x: x.split("/commit")[0])
    df["url"] = df["url"].str.lower()

    # Return modified DataFrame
    return df


def main() -> None:
    # Parse command line
    args: Namespace = cli()

    # Read data from the CSV file
    df: DataFrame = pandas.read_csv(filepath_or_buffer=args.input)

    # Parse for the relevant data
    df = parse_data(df=df)

    # Write data to file
    df.to_json(path_or_buf=args.output, orient="records", index=False, indent=4)


if __name__ == "__main__":
    main()
