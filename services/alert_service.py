import polars as pl
import calendar
from repositories import get_alert_repository


class AlertService:

    @staticmethod
    def get_names():
        df = get_alert_repository().load_data()

        return (
            df.group_by("NAME")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("NAME")
            .to_dicts()
        )

    @staticmethod
    def get_years_by_name(selected_name):
        if not selected_name:
            return []

        df = get_alert_repository().load_data()
        selected_name = str(selected_name).strip()

        result = (
            df.filter(pl.col("NAME") == selected_name)
            .group_by("year_creation")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("year_creation", descending=True)
            .to_dicts()
        )

        return [
            {"year": row["year_creation"], "total_count": row["total_count"]}
            for row in result
        ]

    @staticmethod
    def get_months_by_name_and_year(selected_name, selected_year):
        if not selected_name or selected_year in (None, ""):
            return []

        selected_name = str(selected_name).strip()

        try:
            selected_year = int(selected_year)
        except (TypeError, ValueError):
            return []

        df = get_alert_repository().load_data()

        result = (
            df.filter(
                (pl.col("NAME") == selected_name)
                & (pl.col("year_creation") == selected_year)
            )
            .group_by("mth_creation")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("mth_creation")
            .to_dicts()
        )

        return [
            {"month": calendar.month_name[row["mth_creation"]], "month_number": row["mth_creation"], "total_count": row["total_count"]}
            for row in result
        ]
    
    @staticmethod
    def get_dates(selected_name, selected_year, selected_month):
        if not selected_name or selected_year in (None, "") or selected_month in (None, ""):
            return []

        selected_name = str(selected_name).strip()

        try:
            selected_year = int(selected_year)
        except (TypeError, ValueError):
            return []

        df = get_alert_repository().load_data()

        result = (
            df.filter(
                (pl.col("NAME") == selected_name)
                & (pl.col("year_creation") == int(selected_year))
                & (pl.col("mth_creation") == int(selected_month))
            )
            .group_by("dt_creation")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("dt_creation")
            .to_dicts()
        )

        return [
            {"date": row["dt_creation"].strftime("%d %b %Y"), "total_count": row["total_count"]}
            for row in result
        ]