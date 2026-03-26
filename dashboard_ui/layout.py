from dash import dcc, html

from services.alert_service import AlertService


def build_dashboard_layout():
    names = AlertService.get_names()
    years = AlertService.get_available_years()
    months = AlertService.get_available_months()

    status_options = [
        {"label": item["NAME"], "value": item["NAME"]}
        for item in names
    ]

    year_options = [
        {"label": str(year), "value": year}
        for year in years
    ]

    month_options = months

    return html.Div(
        className="dashboard-shell",
        children=[
            dcc.Store(id="sidebar-collapsed", data=False),

            html.Aside(
                id="dashboard-sidebar",
                className="dashboard-sidebar expanded",
                children=[
                    html.Div(
                        className="sidebar-top",
                        children=[
                            html.Div(
                                className="sidebar-brand",
                                children=[
                                    html.Div("OA", className="brand-logo"),
                                    html.Div(
                                        className="brand-text",
                                        children=[
                                            html.Div("ODD Alerts", className="brand-title"),
                                            html.Div(
                                                "Enterprise Monitoring Dashboard",
                                                className="brand-subtitle",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Button(
                                "☰",
                                id="sidebar-toggle",
                                n_clicks=0,
                                className="sidebar-toggle",
                            ),
                        ],
                    ),
                    html.Div("Navigation", className="sidebar-section-label"),
                    html.Nav(
                        className="sidebar-nav",
                        children=[
                            html.A(
                                "Dashboard",
                                href="/dashboard/",
                                className="sidebar-nav-link active",
                            ),
                            html.A(
                                "Explorer",
                                href="/explorer",
                                className="sidebar-nav-link",
                            ),
                        ],
                    ),
                    html.Div(
                        className="sidebar-info-card",
                        children=[
                            html.Div("Dashboard Notes", className="sidebar-info-title"),
                            html.Ul(
                                className="sidebar-info-list",
                                children=[
                                    html.Li("Use multi-select filters to narrow the analysis."),
                                    html.Li("Switch trend mode between total and per-status comparison."),
                                    html.Li("Use Explorer for detailed date drilldown."),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

            html.Main(
                id="dashboard-main",
                className="dashboard-main expanded",
                children=[
                    html.Div(
                        className="dashboard-page-header",
                        children=[
                            html.H1(
                                "ODD Alerts Monitoring Dashboard",
                                className="dashboard-page-title",
                            ),
                            html.P(
                                "Operational workload, bottleneck signals, and long-term movement for HQ monitoring.",
                                className="dashboard-page-subtitle",
                            ),
                        ],
                    ),

                    html.Div(
                        className="filter-bar-card",
                        children=[
                            html.A(
                                "Reset Filters",
                                href="/dashboard/",
                                className="reset-filter-link",
                            ),
                            html.Div(
                                className="filter-group filter-group-wide",
                                children=[
                                    html.Label("Status", className="filter-label"),
                                    dcc.Dropdown(
                                        id="status-filter",
                                        options=status_options,
                                        value=[],
                                        multi=True,
                                        placeholder="All statuses",
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-group",
                                children=[
                                    html.Label("Year", className="filter-label"),
                                    dcc.Dropdown(
                                        id="year-filter",
                                        options=year_options,
                                        value=[],
                                        multi=True,
                                        placeholder="All years",
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-group",
                                children=[
                                    html.Label("Month", className="filter-label"),
                                    dcc.Dropdown(
                                        id="month-filter",
                                        options=month_options,
                                        value=[],
                                        multi=True,
                                        placeholder="All months",
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-group filter-group-mode",
                                children=[
                                    html.Label("Trend View", className="filter-label"),
                                    dcc.RadioItems(
                                        id="trend-mode",
                                        options=[
                                            {"label": "Total Trend", "value": "total"},
                                            {"label": "Compare Status", "value": "compare"},
                                        ],
                                        value="total",
                                        className="trend-mode-toggle",
                                        labelClassName="trend-mode-option",
                                        inputClassName="trend-mode-input",
                                    ),
                                ],
                            ),
                        ],
                    ),

                    html.Div(id="kpi-row", className="kpi-grid"),

                    html.Section(
                        className="chart-section-card chart-section-large",
                        children=[
                            html.Div("Monthly Trend", className="section-card-title"),
                            html.Div(
                                className="trend-content-grid",
                                children=[
                                    html.Div(
                                        className="trend-chart-panel",
                                        children=[
                                            dcc.Graph(
                                                id="trend-chart",
                                                config={"displaylogo": False, "responsive": True},
                                                className="dashboard-graph dashboard-graph-large",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="trend-insight-panel",
                                        children=[
                                            html.Div("Insights", className="insight-title"),
                                            html.Ul(id="trend-insights", className="insight-list"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),

                    html.Div(
                        className="double-chart-grid",
                        children=[
                            html.Section(
                                className="chart-section-card",
                                children=[
                                    html.Div("Status Distribution", className="section-card-title"),
                                    html.Div(
                                        className="side-insight-grid",
                                        children=[
                                            html.Div(
                                                className="side-chart-panel",
                                                children=[
                                                    dcc.Graph(
                                                        id="status-chart",
                                                        config={"displaylogo": False, "responsive": True},
                                                        className="dashboard-graph",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="side-insight-panel",
                                                children=[
                                                    html.Div("Insights", className="insight-title"),
                                                    html.Ul(id="status-insights", className="insight-list"),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Section(
                                className="chart-section-card",
                                children=[
                                    html.Div("Yearly Breakdown", className="section-card-title"),
                                    html.Div(
                                        className="side-insight-grid yearly-side-insight-grid",
                                        children=[
                                            html.Div(
                                                className="side-chart-panel",
                                                children=[
                                                    dcc.Graph(
                                                        id="yearly-chart",
                                                        config={"displaylogo": False, "responsive": True},
                                                        className="dashboard-graph",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="side-insight-panel",
                                                children=[
                                                    html.Div("Insights", className="insight-title"),
                                                    html.Ul(id="yearly-insights", className="insight-list"),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )