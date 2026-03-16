import polars as pl
from config.settings import DATA_SOURCE, CSV_PATH, PARQUET_PATH, ORACLE_CONFIG

#------------------------------------------------------
# choose which data source to load from based on config
#------------------------------------------------------

def load_alert_data() -> pl.DataFrame:
    if DATA_SOURCE == "csv":
        return _load_from_csv()

    if DATA_SOURCE == "parquet":
        return _load_from_parquet()

    if DATA_SOURCE == "oracle":
        return _load_from_oracle()

    raise ValueError(f"Unsupported data source: {DATA_SOURCE}")

#------------------------------------------------------
# read from respective data source 
#------------------------------------------------------

def _load_from_csv() -> pl.DataFrame:
    df = pl.read_csv(CSV_PATH)
    return _clean_alert_dataframe(df)


def _load_from_parquet() -> pl.DataFrame:
    df = pl.read_parquet(PARQUET_PATH)
    return _clean_alert_dataframe(df)


def _load_from_oracle() -> pl.DataFrame:
    # placeholder until Oracle is really needed
    # later you can implement connection logic here
    raise NotImplementedError("Oracle loader is not implemented yet.")

#------------------------------------------------------
# common cleaning logic for all data sources
#------------------------------------------------------
def _clean_alert_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    # clean column names
    df = df.rename({col: col.strip() for col in df.columns})

    required_columns = {"NAME", "year_creation", "mth_creation", "Count"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    df = df.with_columns([
        pl.col("NAME").cast(pl.Utf8).str.strip_chars(),
        pl.col("year_creation").cast(pl.Int64),
        pl.col("mth_creation").cast(pl.Int64),
        pl.col("Count").cast(pl.Int64),
    ])

    return df