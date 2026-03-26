from flask import Flask

from app.routes.page_routes import register_page_routes
from app.routes.api_routes import register_api_routes
from app.dashboard import create_dashboard


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    register_page_routes(app)
    register_api_routes(app)
    create_dashboard(app)

    return app