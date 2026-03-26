from flask import jsonify, request

from app.services.alert_service import AlertService


def register_api_routes(app):
    @app.route("/api/names")
    def api_names():
        return jsonify(AlertService.get_names())

    @app.route("/api/years")
    def api_years():
        selected_name = request.args.get("name", "")
        if not selected_name:
            return jsonify([])
        return jsonify(AlertService.get_explorer_years(selected_name))

    @app.route("/api/months")
    def api_months():
        selected_name = request.args.get("name", "")
        selected_year = request.args.get("year", "")

        if not selected_name or not selected_year:
            return jsonify([])

        return jsonify(AlertService.get_explorer_months(selected_name, selected_year))

    @app.route("/api/dates")
    def api_dates():
        selected_name = request.args.get("name", "")
        selected_year = request.args.get("year", "")
        selected_month = request.args.get("month", "")

        if not selected_name or not selected_year or not selected_month:
            return jsonify([])

        return jsonify(
            AlertService.get_dates(
                selected_name=selected_name,
                selected_year=selected_year,
                selected_month=selected_month,
            )
        )