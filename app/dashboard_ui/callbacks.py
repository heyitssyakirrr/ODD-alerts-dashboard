import traceback

from dash import Input, Output, State, html

from app.services.alert_service import AlertService
from app.dashboard_ui.figures import (
    build_status_chart,
    build_trend_chart,
    build_yearly_chart,
    empty_figure,
)
from app.dashboard_ui.insights import (
    build_status_insights,
    build_trend_insights,
    build_yearly_insights,
)


def register_dashboard_callbacks(dash_app):
    @dash_app.callback(
        Output("sidebar-collapsed", "data"),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-collapsed", "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(_, current_state):
        return not current_state

    @dash_app.callback(
        Output("dashboard-sidebar", "className"),
        Output("dashboard-main", "className"),
        Input("sidebar-collapsed", "data"),
    )
    def update_sidebar_classes(collapsed):
        if collapsed:
            return "dashboard-sidebar collapsed", "dashboard-main collapsed"
        return "dashboard-sidebar expanded", "dashboard-main expanded"

    @dash_app.callback(
        Output("year-filter", "options"),
        Output("year-filter", "value"),
        Input("status-filter", "value"),
        State("year-filter", "value"),
    )
    def update_year_dropdown(selected_names, current_years):
        try:
            available_years = AlertService.get_available_years(selected_names=selected_names)
            options = [{"label": str(year), "value": year} for year in available_years]

            valid_values = {option["value"] for option in options}
            current_years = current_years or []
            filtered_values = [year for year in current_years if year in valid_values]

            return options, filtered_values
        except Exception:
            traceback.print_exc()
            return [], []

    @dash_app.callback(
        Output("month-filter", "options"),
        Output("month-filter", "value"),
        Input("status-filter", "value"),
        Input("year-filter", "value"),
        State("month-filter", "value"),
    )
    def update_month_dropdown(selected_names, selected_years, current_months):
        try:
            available_months = AlertService.get_available_months(
                selected_names=selected_names,
                selected_years=selected_years,
            )

            valid_values = {option["value"] for option in available_months}
            current_months = current_months or []
            filtered_values = [month for month in current_months if month in valid_values]

            return available_months, filtered_values
        except Exception:
            traceback.print_exc()
            return [], []

    @dash_app.callback(
        Output("kpi-row", "children"),
        Input("status-filter", "value"),
        Input("year-filter", "value"),
        Input("month-filter", "value"),
    )
    def update_kpis(selected_names, selected_years, selected_months):
        try:
            kpis = AlertService.get_kpis(
                selected_names=selected_names,
                selected_years=selected_years,
                selected_months=selected_months,
            )

            cards = [
                ("Total Alerts", f"{kpis['total_alerts']:,}", "purple"),
                ("Open Alerts", f"{kpis['open_alerts']:,}", "blue"),
                ("Closure Rate", f"{kpis['closure_rate']:.1f}%", "green"),
                ("Escalation Rate", f"{kpis['escalation_rate']:.1f}%", "rose"),
            ]

            return [
                html.Div(
                    className=f"kpi-card kpi-{color}",
                    children=[
                        html.Div(label, className="kpi-label"),
                        html.Div(value, className="kpi-value"),
                        html.Div(
                            className="kpi-bar",
                            children=html.Div(className="kpi-bar-fill"),
                        ),
                    ],
                )
                for label, value, color in cards
            ]
        except Exception:
            traceback.print_exc()
            return [
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div("Error", className="kpi-label"),
                        html.Div("Failed to load KPI cards.", className="kpi-value"),
                    ],
                )
            ]

    @dash_app.callback(
        Output("trend-chart", "figure"),
        Output("status-chart", "figure"),
        Output("yearly-chart", "figure"),
        Output("trend-insights", "children"),
        Output("status-insights", "children"),
        Output("yearly-insights", "children"),
        Input("status-filter", "value"),
        Input("year-filter", "value"),
        Input("month-filter", "value"),
        Input("trend-mode", "value"),
    )
    def update_dashboard_content(selected_names, selected_years, selected_months, trend_mode):
        try:
            trend_df = AlertService.get_monthly_trend_df(
                selected_names=selected_names,
                selected_years=selected_years,
                selected_months=selected_months,
                trend_mode=trend_mode,
            )
            status_df = AlertService.get_status_distribution_df(
                selected_names=selected_names,
                selected_years=selected_years,
                selected_months=selected_months,
            )
            yearly_df = AlertService.get_yearly_breakdown_df(
                selected_names=selected_names,
                selected_years=selected_years,
                selected_months=selected_months,
            )

            return (
                build_trend_chart(trend_df, trend_mode=trend_mode),
                build_status_chart(status_df),
                build_yearly_chart(yearly_df),
                build_trend_insights(trend_df, trend_mode=trend_mode),
                build_status_insights(status_df),
                build_yearly_insights(yearly_df),
            )
        except Exception:
            traceback.print_exc()
            return (
                empty_figure("Monthly Trend"),
                empty_figure("Status Distribution"),
                empty_figure("Yearly Breakdown"),
                [html.Li("Failed to generate trend insights.")],
                [html.Li("Failed to generate status insights.")],
                [html.Li("Failed to generate yearly insights.")],
            )