from functools import lru_cache

import polars as pl

from app.config.settings import (
    ALERT_HEADER_PATH,
    WORKFLOW_STATUSES_PATH,
    ODD_EXCLUDED_DOMAIN,
)
from app.repositories.base_repository import BaseAlertRepository


class DeticaParquetAlertRepository(BaseAlertRepository):
    """
    Read raw DETICA parquet files and transform them into the same logical shape
    as the dashboard dataset:
        year_creation | mth_creation | dt_creation | NAME | Count
    """

    def load_data(self) -> pl.DataFrame:
        return _load_detica_dashboard_df()

    def _read_alert_header(self) -> pl.DataFrame:
        df = pl.read_parquet(ALERT_HEADER_PATH)
        return df.rename({col: col.strip() for col in df.columns})

    def _read_workflow_statuses(self) -> pl.DataFrame:
        df = pl.read_parquet(WORKFLOW_STATUSES_PATH)
        return df.rename({col: col.strip() for col in df.columns})

    def _validate_alert_header_schema(self, df: pl.DataFrame) -> None:
        required = {"WW_STATUS_ID", "WW_CREATION_TIMESTAMP", "WW_DOMAIN_CODE"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing columns in alert_header.parquet: {sorted(missing)}"
            )

    def _validate_workflow_statuses_schema(self, df: pl.DataFrame) -> None:
        required = {"ID", "NAME"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing columns in workflow_statuses.parquet: {sorted(missing)}"
            )

    def _filter_odd_alerts(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.filter(
            pl.col("WW_DOMAIN_CODE").cast(pl.Utf8).str.strip_chars() != ODD_EXCLUDED_DOMAIN
        )

    def _join_status_name(
        self,
        alert_header: pl.DataFrame,
        workflow_statuses: pl.DataFrame,
    ) -> pl.DataFrame:
        return alert_header.join(
            workflow_statuses.select(["ID", "NAME"]),
            left_on="WW_STATUS_ID",
            right_on="ID",
            how="left",
        )

    def _aggregate_dashboard_data(self, df: pl.DataFrame) -> pl.DataFrame:
        creation_expr = self._creation_timestamp_expr(df.schema.get("WW_CREATION_TIMESTAMP"))

        return (
            df.with_columns([
                pl.col("NAME").cast(pl.Utf8).str.strip_chars(),
                creation_expr.alias("creation_ts"),
            ])
            .filter(pl.col("creation_ts").is_not_null())
            .with_columns([
                pl.col("creation_ts").dt.year().alias("year_creation"),
                pl.col("creation_ts").dt.month().alias("mth_creation"),
                pl.col("creation_ts").dt.date().alias("dt_creation"),
            ])
            .group_by(["year_creation", "mth_creation", "dt_creation", "NAME"])
            .agg(pl.len().alias("Count"))
            .sort(["NAME", "year_creation", "mth_creation", "dt_creation"])
            .select(["year_creation", "mth_creation", "dt_creation", "NAME", "Count"])
        )

    @staticmethod
    def _creation_timestamp_expr(dtype: pl.DataType) -> pl.Expr:
        if dtype == pl.Date:
            return pl.col("WW_CREATION_TIMESTAMP").cast(pl.Datetime)

        if isinstance(dtype, pl.Datetime):
            return pl.col("WW_CREATION_TIMESTAMP")

        return (
            pl.col("WW_CREATION_TIMESTAMP")
            .cast(pl.Utf8)
            .str.strip_chars()
            .str.strptime(pl.Datetime, strict=False)
        )


@lru_cache(maxsize=1)
def _load_detica_dashboard_df() -> pl.DataFrame:
    repository = DeticaParquetAlertRepository()

    alert_header = repository._read_alert_header()
    workflow_statuses = repository._read_workflow_statuses()

    repository._validate_alert_header_schema(alert_header)
    repository._validate_workflow_statuses_schema(workflow_statuses)

    filtered_alerts = repository._filter_odd_alerts(alert_header)
    joined_df = repository._join_status_name(filtered_alerts, workflow_statuses)

    return repository._aggregate_dashboard_data(joined_df)