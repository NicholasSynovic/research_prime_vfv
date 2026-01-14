import argparse
from datetime import timezone
from pathlib import Path

import pandas as pd
from git import BadName, Repo


def get_args() -> argparse.Namespace:
    """Parses command line arguments for the fix duration analysis."""
    parser = argparse.ArgumentParser(
        description="Calculate the time delta (days) between commit pairs in a Git repo."
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
        help="Path to input CSV with 'commit' and 'future_commit_id' columns",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("time_between_fixes.csv"),
        help="Path for the output CSV (default: time_between_fixes.csv)",
    )
    return parser.parse_args()


def main():
    args = get_args()

    # 1. Load Data
    if not args.input.exists():
        print(f"Error: {args.input} not found.")
        return

    df = pd.read_csv(args.input, sep="|")

    # 2. Initialize Repo
    try:
        repo = Repo(path=args.repo)
    except Exception as e:
        print(f"Error initializing repository: {e}")
        return

    fix_times = []
    start_ts = []
    end_ts = []

    for _, row in df.iterrows():
        try:
            # Extract commit objects
            c_start = repo.commit(rev=row["commit"])
            c_end = repo.commit(rev=row["future_commit_id"])

            # Convert to pandas Timestamps
            ts_start = pd.Timestamp(c_start.committed_datetime)
            ts_end = pd.Timestamp(c_end.committed_datetime)

            # Append calculated values
            start_ts.append(ts_start)
            end_ts.append(ts_end)
            fix_times.append((ts_end - ts_start).days)

        except (BadName, ValueError, KeyError) as e:
            print(f"Warning: Skipping row due to error: {e}")
            start_ts.append(pd.NaT)
            end_ts.append(pd.NaT)
            fix_times.append(None)

    # 3. Update DataFrame
    df["fix_time"] = fix_times
    df["start"] = start_ts
    df["end"] = end_ts

    # 4. Sort and Clean
    # Sort by the start timestamp for chronological analysis
    df = df.sort_values(by="start")

    # 5. Export and Summary
    df.to_csv(args.output, sep="|", index=True)

    # Check for specific outliers (e.g., exactly 120 days)
    # outliers = df[df["fix_time"] == 120]
    # if not outliers.empty:
    #     print("\nPairs with exactly 120 days fix time:")
    #     print(outliers[["commit", "future_commit_id", "fix_time"]])


if __name__ == "__main__":
    main()
