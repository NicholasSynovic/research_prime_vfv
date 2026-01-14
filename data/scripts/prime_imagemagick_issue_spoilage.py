import argparse
import sys
from pathlib import Path

import pandas as pd
from pandas import DataFrame, Timestamp
from progress.bar import Bar


def get_args() -> argparse.Namespace:
    """Parses CLI arguments for issue spoilage calculation."""
    parser = argparse.ArgumentParser(
        description="Compute daily issue spoilage (cumulative age of open issues)."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the input issues CSV file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("issue_spoilage.csv"),
        help="Path for the output CSV (default: issue_spoilage.csv)",
    )
    parser.add_argument(
        "-s",
        "--start-date",
        type=str,
        default="2009-05-09",
        help="Start date for calculation (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--sep", type=str, default="|", help="Separator for input CSV (default: |)"
    )
    return parser.parse_args()


def main():
    args = get_args()

    # 1. Load Data
    try:
        issues_df = pd.read_csv(args.input, sep=args.sep)
        # Ensure timestamps are actual Datetime objects
        issues_df["created_at"] = pd.to_datetime(issues_df["created_at"])
        # If an issue is not closed, we treat it as "closing" in the far future
        issues_df["closed_at"] = pd.to_datetime(issues_df["closed_at"]).fillna(
            Timestamp.now()
        )
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)

    # 2. Setup Date Range
    start_date = Timestamp(args.start_date)
    end_date = Timestamp.now()
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    data = {
        "timestamp": [],
        "issue_spoilage": [],
    }

    # 3. Calculation Loop
    # Optimization: Pre-filtering issues that were closed before our start_date
    relevant_issues = issues_df[issues_df["closed_at"] >= start_date].copy()

    with Bar("Computing Spoilage", max=len(date_range)) as bar:
        for ts in date_range:
            # Active issues: created on/before today AND closed after today
            active_mask = (relevant_issues["created_at"] <= ts) & (
                relevant_issues["closed_at"] > ts
            )
            active_df = relevant_issues[active_mask]

            if active_df.empty:
                spoilage = 0
            else:
                # Spoilage = Sum of (Current Day - Created Date)
                spoilage = (ts - active_df["created_at"]).dt.days.sum()

            data["timestamp"].append(ts)
            data["issue_spoilage"].append(spoilage)
            bar.next()

    # 4. Save Results
    result_df = DataFrame(data)
    result_df.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
