import sqlite3
from pathlib import Path
from sqlite3 import Connection

import pandas as pd
from pandas import DataFrame, Series, Timestamp

CSV_PATH: Path = Path("../../data/vfv_imagemagick_commits.csv")
ISSUE_SPOILAGE_CSV_PATH: Path = Path("../../data/prime_imagemagick_issue_spoilage.csv")
DB_PATH: Path = Path("../../data/prime_imagemagick.sqlite3")


def load_csv(fp: Path, deliminator: str = "|") -> DataFrame:
    return pd.read_csv(filepath_or_buffer=fp, delimiter=deliminator)[
        ["commit", "future_commit_id"]
    ]


def load_issue_spoilage_csv(fp: Path) -> DataFrame:
    df: DataFrame = pd.read_csv(filepath_or_buffer=fp)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_commit_datetimes(db_conn: Connection) -> DataFrame:
    sql_query: str = """
SELECT
  ch.commit_hash,
  c.committed_datetime
FROM
  commit_hashes ch
  JOIN commit_logs c ON ch.id = c.commit_hash_id;
"""
    df: DataFrame = pd.read_sql_query(sql=sql_query, con=db_conn)
    df["committed_datetime"] = pd.to_datetime(df["committed_datetime"])
    df["committed_datetime"] = df["committed_datetime"].dt.floor(freq="d")
    return df


def get_bus_factor_per_day(db_conn: Connection, day: Timestamp) -> int:
    sql_query = f"""
SELECT
  count(committer_id) as bus_factor
FROM
  bus_factor_per_day bf
WHERE
  date(bf.date) = date('{day}');
"""
    return pd.read_sql_query(sql=sql_query, con=db_conn)["bus_factor"][0]


def get_issue_density_per_day(db_conn: Connection, day: Timestamp) -> float:
    sql_query = f"""
SELECT
  CAST(id.open_events as REAL) / id.code as issue_density
FROM
  issue_density_per_day id
WHERE
  date(id.start) = date('{day}');
"""
    return pd.read_sql_query(sql=sql_query, con=db_conn)["issue_density"][0]


def get_issue_spoilage_per_day(issue_spoilage: DataFrame, day: Timestamp) -> int:
    return issue_spoilage[issue_spoilage["timestamp"] == day]["issue_spoilage"].iloc[0]


def main() -> None:
    # Connect to the database
    db_conn: Connection = sqlite3.connect(database=DB_PATH)

    # Create DataFrame of relevant commits and their datetimes
    df_csv: DataFrame = load_csv(fp=CSV_PATH)
    df_issue_spoilage_csv: DataFrame = load_issue_spoilage_csv(
        fp=ISSUE_SPOILAGE_CSV_PATH
    )
    df_commit_datetime: DataFrame = load_commit_datetimes(db_conn=db_conn)
    df_commits: DataFrame = df_commit_datetime[
        df_commit_datetime["commit_hash"].isin(df_csv["commit"])
    ].reset_index(
        drop=True,
    )
    df_future_commits: DataFrame = df_commit_datetime[
        df_commit_datetime["commit_hash"].isin(df_csv["future_commit_id"])
    ].reset_index(
        drop=True,
    )

    # Compute metrics for each commit
    df_commits["bus_factor"] = df_commits["committed_datetime"].apply(
        lambda x: get_bus_factor_per_day(db_conn, x)
    )
    df_commits["issue_density"] = df_commits["committed_datetime"].apply(
        lambda x: get_issue_density_per_day(db_conn, x)
    )
    df_commits["issue_spoilage"] = df_commits["committed_datetime"].apply(
        lambda x: get_issue_spoilage_per_day(df_issue_spoilage_csv, x)
    )

    df_future_commits["bus_factor"] = df_future_commits["committed_datetime"].apply(
        lambda x: get_bus_factor_per_day(db_conn, x)
    )
    df_future_commits["issue_density"] = df_future_commits["committed_datetime"].apply(
        lambda x: get_issue_density_per_day(db_conn, x)
    )
    df_future_commits["issue_spoilage"] = df_future_commits["committed_datetime"].apply(
        lambda x: get_issue_spoilage_per_day(df_issue_spoilage_csv, x)
    )

    # Output CSV files
    df_commits.to_csv(
        path_or_buf="reintroducing_commits.csv", index=True, index_label="index"
    )
    df_future_commits.to_csv(
        path_or_buf="fixing_commits.csv", index=True, index_label="index"
    )

    # Close database connection
    db_conn.close()


if __name__ == "__main__":
    main()
