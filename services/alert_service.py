import calendar
import polars as pl
from repositories import get_alert_repository


class AlertService:
    _repository = get_alert_repository()

    @classmethod
    def _load_df(cls) -> pl.DataFrame:
        return cls._repository.load_data()

    @staticmethod
    def _normalize_to_list(value):
        if value in (None, "", "ALL"):
            return []

        if isinstance(value, (list, tuple, set)):
            normalized = [item for item in value if item not in (None, "", "ALL")]
            return normalized

        return [value]

    @classmethod
    def _apply_filters(
        cls,
        df: pl.DataFrame,
        selected_names=None,
        selected_years=None,
        selected_months=None,
    ) -> pl.DataFrame:
        names = cls._normalize_to_list(selected_names)
        years = cls._normalize_to_list(selected_years)
        months = cls._normalize_to_list(selected_months)

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

    @classmethod
    def get_names(cls):
        df = cls._load_df()

        return (
            df.group_by("NAME")
            .agg(pl.col("Count").sum().alias("total_count"))
            .sort("NAME")
            .to_dicts()
        )

    @classmethod
    def get_available_years(cls, selected_names=None):
        df = cls._apply_filters(cls._load_df(), selected_names=selected_names)

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
        df = cls._apply_filters(
            cls._load_df(),
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

    @classmethod
    def get_kpis(cls, selected_names=None, selected_years=None, selected_months=None):
        df = cls._apply_filters(
            cls._load_df(),
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

        closed_df = df.filter(pl.col("NAME").cast(pl.Utf8).str.starts_with("Closed"))
        open_df = df.filter(~pl.col("NAME").cast(pl.Utf8).str.starts_with("Closed"))
        escalated_df = df.filter(pl.col("NAME") == "Escalated")

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
        df = cls._apply_filters(
            cls._load_df(),
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
        df = cls._apply_filters(
            cls._load_df(),
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
        df = cls._apply_filters(
            cls._load_df(),
            selected_names=selected_names,
            selected_years=selected_years,
            selected_months=selected_months,
        )

        return (
            df.group_by(["NAME", "year_creation"])
            .agg(pl.col("Count").sum().alias("Count"))
            .sort(["year_creation", "NAME"])
        )