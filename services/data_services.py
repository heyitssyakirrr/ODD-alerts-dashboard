from pathlib import Path
import polars as pl

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "odd_alerts.csv"


def load_data():
    df = pl.read_csv(CSV_PATH)

    # clean column names just in case there are extra spaces
    df = df.rename({col: col.strip() for col in df.columns})

    # clean string columns
    df = df.with_columns([
        pl.col("NAME").cast(pl.Utf8).str.strip_chars(),
        pl.col("year_creation").cast(pl.Int64),
        pl.col("mth_creation").cast(pl.Int64),
        pl.col("Count").cast(pl.Int64)
    ])

    return df


def get_names():
    df = load_data()

    result = (
        df.group_by("NAME")
        .agg(pl.col("Count").sum().alias("total_count"))
        .sort("NAME")
        .to_dicts()
    )

    return result


def get_years_by_name(selected_name):

    if not selected_name:
        return []

    selected_name = str(selected_name).strip()

    df = load_data()

    result = (
        df.filter(pl.col("NAME") == selected_name)
        .group_by("year_creation")
        .agg(pl.col("Count").sum().alias("total_count"))
        .sort("year_creation", descending=True)
        .to_dicts()
    )

    return [
        {
            "year": row["year_creation"],
            "total_count": row["total_count"]
        }
        for row in result
    ]


def get_months_by_name_and_year(selected_name, selected_year):

    if not selected_name or not selected_year:
        return []

    selected_name = str(selected_name).strip()

    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        return []

    df = load_data()

    result = (
        df.filter(
            (pl.col("NAME") == selected_name) &
            (pl.col("year_creation") == int(selected_year))
        )
        .group_by("mth_creation")
        .agg(pl.col("Count").sum().alias("total_count"))
        .sort("mth_creation")
        .to_dicts()
    )

    return [
        {
            "month": row["mth_creation"],
            "total_count": row["total_count"]
        }
        for row in result
    ]