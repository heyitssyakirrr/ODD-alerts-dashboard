import calendar
import polars as pl

from app.services.data_service import AlertDataService
from app.services.filter_utils import apply_filters

# retrieve the available filter options for the dropdowns in the frontend

class FilterOptionService:
    @classmethod
    def get_names(cls):
        df = AlertDataService.load_df()
        return (
            df.group_by("NAME")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("NAME")
            .to_dicts()
        )

    @classmethod
    def get_available_years(cls, selected_names=None):
        df = apply_filters(AlertDataService.load_df(), selected_names=selected_names)

        years = (
            df.select("year_creation")
            .drop_nulls()
            .unique()
            .sort("year_creation")
            .to_series()
            .to_list()
        )

        return [int(year) for year in years]

    @classmethod
    def get_available_months(cls, selected_names=None, selected_years=None):
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_names,
            selected_years=selected_years,
        )

        months = (
            df.select("mth_creation")
            .drop_nulls()
            .unique()
            .sort("mth_creation")
            .to_series()
            .to_list()
        )

        return [
            {
                "label": calendar.month_name[int(month)],
                "value": int(month),
            }
            for month in months
        ]