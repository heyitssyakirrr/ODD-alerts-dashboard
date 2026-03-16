import polars as pl
from loaders.alert_loader import load_alert_data


class AlertService:
    @staticmethod
    def get_names():
        df = load_alert_data()

        result = (
            df.group_by("NAME")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("NAME")
            .to_dicts()
        )

        return result

    @staticmethod
    def get_years_by_name(selected_name):
        if not selected_name:
            return []

        selected_name = str(selected_name).strip()
        df = load_alert_data()

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

    @staticmethod
    def get_months_by_name_and_year(selected_name, selected_year):
        if not selected_name or not selected_year:
            return []

        selected_name = str(selected_name).strip()

        try:
            selected_year = int(selected_year)
        except (TypeError, ValueError):
            return []

        df = load_alert_data()

        result = (
            df.filter(
                (pl.col("NAME") == selected_name) &
                (pl.col("year_creation") == selected_year)
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