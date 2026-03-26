import polars as pl


def normalize_to_list(value):
    if value in (None, "", "ALL"):
        return []

    if isinstance(value, (list, tuple, set)):
        return [item for item in value if item not in (None, "", "ALL")]

    return [value]


def apply_filters(
    df: pl.DataFrame,
    selected_names=None,
    selected_years=None,
    selected_months=None,
) -> pl.DataFrame:
    names = normalize_to_list(selected_names)
    years = normalize_to_list(selected_years)
    months = normalize_to_list(selected_months)

    if names:
        names = [str(name).strip() for name in names]
        df = df.filter(pl.col("NAME").is_in(names))

    if years:
        try:
            years = [int(year) for year in years]
        except (TypeError, ValueError):
            return df.head(0)
        df = df.filter(pl.col("year_creation").is_in(years))

    if months:
        try:
            months = [int(month) for month in months]
        except (TypeError, ValueError):
            return df.head(0)
        df = df.filter(pl.col("mth_creation").is_in(months))

    return df