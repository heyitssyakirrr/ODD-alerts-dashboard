from flask import Flask, render_template, jsonify, request, redirect
from services.alert_service import AlertService
from dashboard import create_dashboard

app = Flask(__name__)


@app.route("/")
def home():
    return redirect("/dashboard/")


@app.route("/explorer")
def index():
    return render_template("index.html")


@app.route("/api/names")
def api_names():
    return jsonify(AlertService.get_names())


@app.route("/api/years")
def api_years():
    selected_name = request.args.get("name", "")
    if not selected_name:
        return jsonify([])
    return jsonify(AlertService.get_years_by_name(selected_name))


@app.route("/api/months")
def api_months():
    selected_name = request.args.get("name", "")
    selected_year = request.args.get("year", "")

    if not selected_name or not selected_year:
        return jsonify([])

    return jsonify(AlertService.get_months_by_name_and_year(selected_name, selected_year))


@app.route("/api/dates")
def api_dates():
    selected_name = request.args.get("name", "")
    selected_year = request.args.get("year", "")
    selected_month = request.args.get("month", "")

    if not selected_name or not selected_year or not selected_month:
        return jsonify([])

    return jsonify(AlertService.get_dates(selected_name, selected_year, selected_month))


dash_app = create_dashboard(app)

if __name__ == "__main__":
    app.run(debug=True)