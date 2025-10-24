from argparse import ArgumentParser, Namespace
from collections import defaultdict
from datetime import timezone
from math import ceil, floor
from pathlib import Path

import pandas as pd
from git import Repo

IMAGEMAGICK_PATH: Path = Path("~/Documents/.temp/ImageMagick")


def read_csv() -> pd.DataFrame:
    return pd.read_csv(
        filepath_or_buffer=Path("../../data/ImageMagick VFV Commits.csv"),
        sep="|",
    )


df: pd.DataFrame = read_csv()

repo: Repo = Repo(path=IMAGEMAGICK_PATH)

data: dict[str, list[int]] = {
    "fix_time": [],
    "start": [],
    "end": [],
}

row: pd.Series
for _, row in df.iterrows():
    commit: str = row["commit"]
    future_commit: str = row["future_commit_id"]

    commit_ts: pd.Timestamp = pd.Timestamp(
        ts_input=repo.commit(rev=commit).committed_datetime,
        unit="s",
    )
    future_commit_ts: pd.Timestamp = pd.Timestamp(
        ts_input=repo.commit(rev=future_commit).committed_datetime,
        unit="s",
    )

    data["fix_time"].append((future_commit_ts - commit_ts).days)
    data["start"].append(commit_ts)
    data["end"].append(future_commit_ts)

df["fix_time"] = data["fix_time"]
df["start"] = data["start"]
df["end"] = data["end"]
df = df.sort_values(by="start")

df.to_csv(path_or_buf="time_between_fixes.csv", sep="|")

print(df[df["fix_time"] == 120][["commit", "future_commit_id"]])
