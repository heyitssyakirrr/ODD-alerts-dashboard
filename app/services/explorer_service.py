import calendar
import polars as pl

from app.services.data_service import AlertDataService
from app.services.filter_utils import apply_filters


class ExplorerService:
    @classmethod
    def get_explorer_years(cls, selected_name):
        df = apply_filters(AlertDataService.load_df(), selected_names=selected_name)

        if df.is_empty():
            return []

        return (
            df.group_by("year_creation")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("year_creation", descending=True)
            .rename({"year_creation": "year"})
            .with_columns(pl.col("year").cast(pl.Int64))
            .to_dicts()
        )

    @classmethod
    def get_explorer_months(cls, selected_name, selected_year):
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_name,
            selected_years=selected_year,
        )

        if df.is_empty():
            return []

        result = (
            df.group_by("mth_creation")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("mth_creation")
            .with_columns([
                pl.col("mth_creation").alias("month_number"),
                pl.col("mth_creation").map_elements(
                    lambda x: calendar.month_name[int(x)],
                    return_dtype=pl.Utf8,
                ).alias("month"),
            ])
            .select(["month", "month_number", "total_count"])
        )

        return result.to_dicts()

    @classmethod
    def get_dates(cls, selected_name, selected_year, selected_month):
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_name,
            selected_years=selected_year,
            selected_months=selected_month,
        )

        if df.is_empty() or "dt_creation" not in df.columns:
            return []

        result = (
            df.group_by("dt_creation")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("dt_creation")
            .with_columns(pl.col("dt_creation").cast(pl.Utf8).alias("date"))
            .select(["date", "total_count"])
        )

        return result.to_dicts()