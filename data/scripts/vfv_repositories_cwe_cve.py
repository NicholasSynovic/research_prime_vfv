"""
Convert VulFixVul CSV dataset into a JSON file

Copyright Nicholas M. Synovic, 2025

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

import pandas as pd


def cli() -> Namespace:
    """
    CLI interface for VulFixVul Dataset Conversion

    This function implements a command-line interface (CLI) tool designed to
    facilitate the conversion of datasets from the VulFixVul project's CSV
    format into JSON. The CLI tool allows users to specify input and output file
    paths through straightforward command-line arguments, ensuring that data can
    be processed efficiently without manual intervention.

    Key Features:
    - Argument Parsing: Utilizes Python's `argparse` module to define and parse
        command-line options for specifying the input CSV file path (`-i`,
        `--input`) and the desired output JSON file path (`-o`, `--output`).
        Both paths are validated as absolute resolutions of specified locations.
    - Required Arguments: Ensures that both an input CSV file and an output JSON
        file path are provided by setting required flags for these arguments,
        enhancing usability and reducing errors associated with incomplete data
        processing pipelines.
    - Path Resolution: Automatically resolves provided paths to their canonical
        form using `Path(x).resolve()`, ensuring compatibility across different
        operating systems and user environments.

    Usage:
    - The CLI tool is intended for direct execution from the command line or
        terminal. Users invoke it by specifying the paths to their input CSV
        file and desired output JSON file, leveraging the defined arguments.

    """
    # Command line argument parser
    parser: ArgumentParser = ArgumentParser(
        prog="VulFixVul Repository Extractor",
    )

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


def parse_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse VulFixVul CSV Dataset into JSON

    This function is designed to preprocess and normalize data extracted from
    the VulFixVul CSV dataset, preparing it for conversion into a JSON format.
    The preprocessing steps include filtering relevant columns, standardizing
    column names for consistency, transforming URL formats to ensure uniformity
    across records, and ensuring case normalization.

    Parameters:
        df: pd.DataFrame
            A pandas DataFrame containing raw data from the VulFixVul project's
            CSV file. This DataFrame is expected to include at least the
            following columns: 'Project', 'codeLink', 'CWE ID', 'CVE ID', and
            potentially others related to commit URLs among other fields not
            directly relevant for this transformation.

    Returns:
        pd.DataFrame
            A modified pandas DataFrame with the following transformations
            applied:
            - Columns filtered to only include 'Project', 'codeLink', 'CWE ID',
                and 'CVE ID'.
            - Column names normalized to lowercase and spaces replaced with
                underscores.
            - Specific column renaming from 'codelink' to 'url'.
            - URLs extracted by stripping commit hashes (indicated by '/commit')
                and converting all URL strings to lowercase for consistency.

    Usage:
    - This function is typically invoked as part of a larger data conversion
        pipeline, specifically within the context of transforming VulFixVul
        dataset CSV files into JSON format. It prepares the DataFrame for
        further normalization steps or directly outputs it in JSON format after
        additional processing.

    """
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
    """
    The application entrypoint.

    This function orchestrates the complete process of converting a VulFixVul
    CSV dataset into JSON format. It serves as the entry point when executing
    the script directly and integrates all key components: CLI argument parsing,
    data reading from CSV, transformation logic application, and final output
    writing to JSON.

    Key Steps:
    1. CLI Argument Parsing (`cli`): Initiates by invoking `cli()` to parse
        command-line arguments provided by the user. This step ensures that
        paths for both input CSV files (required) and output JSON files (also
        required) are correctly specified.
    2. Data Reading (`pd.read_csv`): Utilizes pandas' `read_csv` function to
        load data from the specified CSV file into a DataFrame. The path to this
        CSV file is obtained directly from the parsed CLI arguments, ensuring
        that the correct dataset is processed.
    3. Data Parsing and Transformation (`parse_data(df)`): Applies a series of
        transformations to the DataFrame:
    - Filters columns to include only those relevant for JSON serialization
        ('Project', 'codeLink', 'CWE ID', 'CVE ID').
    - Normalizes column names by converting them to lowercase and replacing
        spaces with underscores.
    - Renames specific columns (e.g., changing 'codelink' to 'url') and
        transforms URLs within these columns into GitHub-compatible formats,
        ensuring consistency across records.
    4. Data Serialization (`df.to_json`): Writes the transformed DataFrame to a
        JSON file specified by the user through CLI arguments. The serialization
        process includes:
    - Setting `orient="records"` for a list of records format.
    - Disabling index inclusion with `index=False`.
    - Preserving indentation (`indent=4`) for readability.

    Usage:
    - This function is designed to be invoked directly from the command line or
    terminal, serving as the main program logic. It abstracts away the
    complexities of data processing and file handling, providing a seamless
    conversion experience.
    """
    # Parse command line
    args: Namespace = cli()

    # Read data from the CSV file
    df: pd.DataFrame = pd.read_csv(filepath_or_buffer=args.input)

    # Parse for the relevant data
    df = parse_data(df=df)

    # Write data to file
    df.to_json(path_or_buf=args.output, orient="records", index=False, indent=4)


if __name__ == "__main__":
    main()
