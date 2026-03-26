from app.services.analytics_service import AnalyticsService
from app.services.explorer_service import ExplorerService
from app.services.filter_option_service import FilterOptionService


class AlertService:
    get_names = FilterOptionService.get_names
    get_available_years = FilterOptionService.get_available_years
    get_available_months = FilterOptionService.get_available_months

    get_explorer_years = ExplorerService.get_explorer_years
    get_explorer_months = ExplorerService.get_explorer_months
    get_dates = ExplorerService.get_dates

    get_kpis = AnalyticsService.get_kpis
    get_status_distribution_df = AnalyticsService.get_status_distribution_df
    get_monthly_trend_df = AnalyticsService.get_monthly_trend_df
    get_yearly_breakdown_df = AnalyticsService.get_yearly_breakdown_df