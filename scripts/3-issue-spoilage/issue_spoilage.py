import pandas
from pandas import DataFrame, Series, Timestamp
from progress.bar import Bar

POINTER_DATE: Timestamp = Timestamp(ts_input="09-05-2009")
ENDING_DATE: Timestamp = Timestamp.now()
DATE_RANGE = pandas.date_range(start=POINTER_DATE, end=ENDING_DATE, freq="D")

# Load data
issues_df: DataFrame = pandas.read_csv(
    filepath_or_buffer="../../data/issues.csv", sep="|"
)

# Set proper column types
issues_df["created_at"] = issues_df["created_at"].apply(Timestamp)
issues_df["closed_at"] = issues_df["closed_at"].apply(Timestamp)

data: dict[str, list[Timestamp | int]] = {
    "timestamp": [],
    "issue_spoilage": [],
}


with Bar("Computing...", max=(ENDING_DATE - POINTER_DATE).days) as bar:
    ts: Timestamp
    for ts in DATE_RANGE:
        df: DataFrame = issues_df.copy()
        df = df[df["created_at"] <= ts]
        df = df[df["closed_at"] > ts]
        if df.empty:
            data["timestamp"].append(ts)
            data["issue_spoilage"].append(0)
            bar.next()
            continue

        df["issue_spoilage"] = df["created_at"].apply(lambda x: (ts - x).days)

        data["timestamp"].append(ts)
        data["issue_spoilage"].append(df["issue_spoilage"].sum())

        bar.next()

DataFrame(data=data).to_csv(path_or_buf="issue_spoilage.csv")
