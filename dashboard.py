from dash import Dash

from dashboard_ui.layout import build_dashboard_layout
from dashboard_ui.callbacks import register_dashboard_callbacks


def create_dashboard(server):
    dash_app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/dashboard/",
        requests_pathname_prefix="/dashboard/",
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "/static/style.css",
            "/static/dashboard.css",
        ],
    )

    dash_app.title = "ODD Alerts Dashboard"
    dash_app.layout = build_dashboard_layout()
    register_dashboard_callbacks(dash_app)

    return dash_app