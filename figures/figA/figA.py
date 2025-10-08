from pathlib import Path

import click
import pandas
from pandas import DataFrame
from sqlalchemy import Engine, create_engine


@click.command()
@click.option(
    "-i",
    "--input-db",
    type=lambda x: Path(x).resolve(),
    help="Path to PRIME database",
    required=True,
)
@click.option(
    "-o",
    "--output-fig",
    type=lambda x: Path(x).resolve(),
    help="Path to write figure",
    required=False,
    default="figA.pdf",
    show_default=True,
)
def main(input_db: Path, output_fig: Path)  ->  None:
    db: Engine = create_engine(url:f"sqlite:///{input_db}")
    df: DataFrame = pandas.read_sql_table(table_name="bus_factor_per_day", con=db, index_col="id",)

    print(df)

if __name__ == "__main__":
    main()
