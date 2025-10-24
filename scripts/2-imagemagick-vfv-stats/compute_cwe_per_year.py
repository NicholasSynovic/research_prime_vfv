from argparse import ArgumentParser, Namespace
from collections import defaultdict
from datetime import timezone
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

data: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

row: pd.Series
for _, row in df.iterrows():
    committed_timestamp: pd.Timestamp = pd.Timestamp(
        ts_input=repo.commit(rev=row["commit"]).committed_date,
        tz=timezone.utc,
        unit="s",
    )

    for cwe in row["CWE ID"].split(","):
        data[cwe][committed_timestamp.year] += 1

# commit: str
# for commit in df["future_commit_id"]:
#     committed_timestamp: pd.Timestamp = pd.Timestamp(ts_input=repo.commit(rev=commit).committed_date,tz=timezone.utc, unit="s",)
#     data["future_commit"][committed_timestamp.year] += 1

print(pd.DataFrame(data).fillna(value=0).astype(dtype=int).sum().sort_values())


# df = pd.DataFrame(data).sort_index().fillna(value=0).astype(dtype=int)
# df.to_csv(path_or_buf="cwe_per_year.csv")
