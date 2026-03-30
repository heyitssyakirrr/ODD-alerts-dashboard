import calendar
import polars as pl

from app.services.data_service import AlertDataService
from app.services.filter_utils import apply_filters


class AnalyticsService:
    @classmethod
    def get_kpis(cls, selected_names=None, selected_years=None, selected_months=None):
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_names,
            selected_years=selected_years,
            selected_months=selected_months,
        )

        if df.is_empty():
            return {
                "total_alerts": 0,
                "open_alerts": 0,
                "closure_rate": 0.0,
                "escalation_rate": 0.0,
            }

        total_alerts = int(df["Count"].sum())

        closed_df = df.filter(pl.col("NAME").cast(pl.Utf8).str.starts_with("Closed")) # not sure about closed - rejected or accepeted
        open_df = df.filter(~pl.col("NAME").cast(pl.Utf8).str.starts_with("Closed"))
        escalated_df = df.filter(pl.col("NAME") == "Escalated") # assuming there's a specific status for escalated alerts

        closed_alerts = int(closed_df["Count"].sum()) if closed_df.height else 0
        open_alerts = int(open_df["Count"].sum()) if open_df.height else 0
        escalated_alerts = int(escalated_df["Count"].sum()) if escalated_df.height else 0

        closure_rate = (closed_alerts / total_alerts * 100) if total_alerts else 0.0
        escalation_rate = (escalated_alerts / total_alerts * 100) if total_alerts else 0.0

        return {
            "total_alerts": total_alerts,
            "open_alerts": open_alerts,
            "closure_rate": round(closure_rate, 1),
            "escalation_rate": round(escalation_rate, 1),
        }

    @classmethod
    def get_status_distribution_df(
        cls,
        selected_names=None,
        selected_years=None,
        selected_months=None,
    ) -> pl.DataFrame:
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_names,
            selected_years=selected_years,
            selected_months=selected_months,
        )

        return (
            df.group_by("NAME")
            .agg(pl.col("Count").sum().alias("Count"))
            .sort("Count", descending=True)
        )

    @classmethod
    def get_monthly_trend_df(
        cls,
        selected_names=None,
        selected_years=None,
        selected_months=None,
        trend_mode="total",
    ) -> pl.DataFrame:
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_names,
            selected_years=selected_years,
            selected_months=selected_months,
        )

        if df.is_empty():
            return df

        if trend_mode == "compare":
            result = (
                df.group_by(["NAME", "year_creation", "mth_creation"])
                .agg(pl.col("Count").sum().alias("Count"))
                .sort(["year_creation", "mth_creation", "NAME"])
            )
        else:
            result = (
                df.group_by(["year_creation", "mth_creation"])
                .agg(pl.col("Count").sum().alias("Count"))
                .sort(["year_creation", "mth_creation"])
            )

        result = result.with_columns(
            (
                pl.col("mth_creation").map_elements(
                    lambda x: calendar.month_abbr[x],
                    return_dtype=pl.Utf8,
                )
                + pl.lit(" ")
                + pl.col("year_creation").cast(pl.Utf8)
            ).alias("period_label"),
            (
                pl.col("year_creation") * 100 + pl.col("mth_creation")
            ).alias("period_order"),
        )

        return result

    @classmethod
    def get_yearly_breakdown_df(
        cls,
        selected_names=None,
        selected_years=None,
        selected_months=None,
    ) -> pl.DataFrame:
        df = apply_filters(
            AlertDataService.load_df(),
            selected_names=selected_names,
            selected_years=selected_years,
            selected_months=selected_months,
        )

        return (
            df.group_by(["NAME", "year_creation"])
            .agg(pl.col("Count").sum().alias("Count"))
            .sort(["year_creation", "NAME"])
        )