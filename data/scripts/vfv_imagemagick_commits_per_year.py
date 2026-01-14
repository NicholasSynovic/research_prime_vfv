import argparse
from collections import defaultdict
from datetime import timezone
from pathlib import Path

import pandas as pd
from git import BadName, Repo


def get_args() -> argparse.Namespace:
    """Parses command line arguments for the commit analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze commit frequency per year from a CSV and a Git repository."
    )
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to the local ImageMagick git repository",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the input CSV file containing commit IDs",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("commits_per_year.csv"),
        help="Path where the output CSV will be saved (default: commits_per_year.csv)",
    )
    parser.add_argument(
        "--sep",
        type=str,
        default="|",
        help="Separator used in the input CSV (default: |)",
    )
    return parser.parse_args()


def count_commits_by_year(repo: Repo, commit_ids: pd.Series) -> dict[int, int]:
    """
    Iterates through a series of commit IDs and counts occurrences per year.

    Args:
        repo: The git.Repo object.
        commit_ids: A pandas Series of commit hashes.

    Returns:
        A dictionary where keys are years (int) and values are commit counts (int).
    """
    counts = defaultdict(int)
    for sha in commit_ids.dropna():
        try:
            # Get the commit object from the repo
            commit_obj = repo.commit(rev=sha)
            # Convert Unix timestamp to UTC year
            year = pd.Timestamp(
                ts_input=commit_obj.committed_date,
                tz=timezone.utc,
                unit="s",
            ).year
            counts[year] += 1
        except (BadName, ValueError):
            print(f"Warning: Commit {sha} not found in repository. Skipping.")
            continue
    return dict(counts)


def main():
    args = get_args()

    # 1. Load the CSV data
    if not args.input.exists():
        print(f"Error: Input file {args.input} does not exist.")
        return

    df_input = pd.read_csv(filepath_or_buffer=args.input, sep=args.sep)

    # 2. Initialize the Git repository
    try:
        repo = Repo(path=args.repo)
    except Exception as e:
        print(f"Error initializing repository at {args.repo}: {e}")
        return

    # 3. Process commit columns
    commit_counts = count_commits_by_year(repo, df_input["commit"])
    future_commit_counts = count_commits_by_year(repo, df_input["future_commit_id"])

    # 4. Combine data and format DataFrame
    data = {
        "commit": commit_counts,
        "future_commit": future_commit_counts,
    }

    # .sort_index() ensures the years are in chronological order
    df_result = pd.DataFrame(data).sort_index().fillna(0).astype(int)

    # 5. Export results
    df_result.to_csv(path_or_buf=args.output)


if __name__ == "__main__":
    main()
