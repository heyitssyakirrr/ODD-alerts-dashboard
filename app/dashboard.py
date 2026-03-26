from dash import Dash

from app.dashboard_ui.layout import build_dashboard_layout
from app.dashboard_ui.callbacks import register_dashboard_callbacks


def create_dashboard(server):
    dash_app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/dashboard/",
        requests_pathname_prefix="/dashboard/",
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "/static/explorer.css",
            "/static/dashboard.css",
        ],
    )

    dash_app.title = "ODD Alerts Dashboard"
    dash_app.layout = build_dashboard_layout()
    register_dashboard_callbacks(dash_app)

    return dash_app