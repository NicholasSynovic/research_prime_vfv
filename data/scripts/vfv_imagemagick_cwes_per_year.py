import argparse
from collections import defaultdict
from datetime import timezone
from pathlib import Path

import pandas as pd
from git import BadName, Repo


def get_args() -> argparse.Namespace:
    """Parses command line arguments for the CWE analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze the frequency of CWE IDs per year from a Git repository."
    )
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to the local git repository",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the input CSV file containing 'commit' and 'CWE ID' columns",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("cwe_per_year.csv"),
        help="Path for the output CSV (default: cwe_per_year.csv)",
    )
    return parser.parse_args()


def main():
    args = get_args()

    # 1. Load Data
    if not args.input.exists():
        print(f"Error: {args.input} not found.")
        return

    df_input = pd.read_csv(args.input, sep="|")

    # 2. Initialize Repo
    try:
        repo = Repo(path=args.repo)
    except Exception as e:
        print(f"Error initializing repository: {e}")
        return

    # Nested dict structure: data[year][cwe_id] = count
    stats = defaultdict(lambda: defaultdict(int))

    for _, row in df_input.iterrows():
        sha = row["commit"]
        cwe_field = str(row["CWE ID"])

        try:
            # Extract year from git commit
            commit_obj = repo.commit(rev=sha)
            year = pd.Timestamp(
                ts_input=commit_obj.committed_date,
                tz=timezone.utc,
                unit="s",
            ).year

            # Handle multiple CWEs (split by comma and strip whitespace)
            cwe_list = [c.strip() for c in cwe_field.split(",") if c.strip()]

            for cwe in cwe_list:
                stats[year][cwe] += 1

        except (BadName, ValueError):
            print(f"Warning: Commit {sha} not found. Skipping.")
            continue

    # 3. Transform data into DataFrame
    # Columns will be CWE IDs, Rows will be Years
    df_result = pd.DataFrame(stats).T.sort_index().fillna(0).astype(int)
    df_result.index.name = "Year"

    # 4. Console Summary (Total occurrences per CWE across all years)
    # print("\nSummary of CWE Totals:")
    # print(df_result.sum().sort_values(ascending=False))

    # 5. Export
    df_result.to_csv(args.output)


if __name__ == "__main__":
    main()
